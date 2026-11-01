"""Local adapter conformance without contacting a model server or downloading a tokenizer."""

import asyncio
import json
from typing import Any

import httpx
import pytest
from tokenizers.pre_tokenizers import ByteLevel

from apps.decision_program.baseline import Message
from apps.decision_program.ollama_backend import (
    BASE_URL,
    MODEL_ID,
    PINNED_MANIFEST,
    PINNED_VERSION,
    OllamaQwen3Backend,
    check_server,
)
from apps.decision_program.qwen3_tokenizer import Qwen3Tokenizer, render_chat


def toy_metadata() -> dict[str, Any]:
    # A deliberately tiny synthetic BPE fixture; not a Qwen model or token estimate.
    alphabet = sorted(ByteLevel.alphabet())
    extra = [
        "12",
        "He",
        "Hel",
        "Hell",
        "Hello",
        "<|im_start|>",
        "<|im_end|>",
        "<think>",
        "</think>",
    ]
    return {
        "tokenizer.ggml.model": "gpt2",
        "tokenizer.ggml.pre": "qwen2",
        "tokenizer.ggml.add_bos_token": False,
        "tokenizer.ggml.tokens": alphabet + extra,
        "tokenizer.ggml.token_type": [1] * (len(alphabet) + 5) + [3] * 4,
        "tokenizer.ggml.merges": ["1 2", "H e", "He l", "Hel l", "Hell o"],
    }


@pytest.fixture
def tokenizer() -> Qwen3Tokenizer:
    return Qwen3Tokenizer(toy_metadata())


def test_bpe_pattern_special_tokens_and_stable_identity(tokenizer: Qwen3Tokenizer) -> None:
    assert len(tokenizer.encode("Hello")) == 1
    assert len(tokenizer.encode("12")) == 2  # Qwen splits digits before BPE merging.
    assert len(tokenizer.encode("<|im_start|>")) == 1
    assert tokenizer.identity_sha256 == Qwen3Tokenizer(toy_metadata()).identity_sha256
    changed = toy_metadata()
    changed["tokenizer.ggml.merges"] = changed["tokenizer.ggml.merges"][:-1]
    assert Qwen3Tokenizer(changed).identity_sha256 != tokenizer.identity_sha256


@pytest.mark.parametrize(
    "field,value",
    [
        ("tokenizer.ggml.pre", "other"),
        ("tokenizer.ggml.model", "llama"),
        ("tokenizer.ggml.add_bos_token", True),
        ("tokenizer.ggml.add_eos_token", True),
    ],
)
def test_reject_other_tokenization_profiles(field: str, value: Any) -> None:
    info = toy_metadata()
    info[field] = value
    with pytest.raises(ValueError, match="unsupported tokenizer"):
        Qwen3Tokenizer(info)


def test_fixed_chat_template_keeps_message_contents_verbatim(tokenizer: Qwen3Tokenizer) -> None:
    messages = (Message("system", "rule"), Message("user", '{"text":"{untrusted}"}'))
    raw = render_chat(messages)
    assert raw == (
        "<|im_start|>system\nrule<|im_end|>\n"
        '<|im_start|>user\n{"text":"{untrusted}"} /no_think<|im_end|>\n'
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )
    assert tokenizer.count(messages) == len(tokenizer.encode(raw))
    with pytest.raises(ValueError, match="exactly one"):
        render_chat((messages[0],))


def call_backend(tokenizer: Qwen3Tokenizer, transport: httpx.MockTransport) -> Any:
    backend = OllamaQwen3Backend(tokenizer, transport=transport)
    return asyncio.run(
        backend.generate(
            (Message("system", "rule"), Message("user", "Hello")),
            seed=101,
            temperature=0.0,
            top_p=1.0,
            max_output_tokens=512,
            timeout_ms=30000,
        )
    )


def test_raw_request_is_local_bounded_and_without_json_repair(tokenizer: Qwen3Tokenizer) -> None:
    seen = []

    def handle(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(BASE_URL)
        seen.append(request.url.path)
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": PINNED_VERSION})
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": MODEL_ID, "digest": PINNED_MANIFEST}]}
            )
        payload = json.loads(request.content)
        assert payload["raw"] and not payload["think"] and not payload["stream"]
        assert set(payload) == {
            "model",
            "prompt",
            "raw",
            "think",
            "stream",
            "keep_alive",
            "options",
        }
        assert payload["options"] == {
            "seed": 101,
            "temperature": 0.0,
            "top_p": 1.0,
            "top_k": 0,
            "min_p": 0.0,
            "repeat_penalty": 1.0,
            "num_ctx": 8704,
            "num_predict": 512,
            "stop": ["<|im_start|>", "<|im_end|>"],
        }
        return httpx.Response(
            200,
            json={
                "model": MODEL_ID,
                "done": True,
                "done_reason": "stop",
                "response": "not repaired",
                "prompt_eval_count": 42,
                "eval_count": 3,
            },
        )

    completion = call_backend(tokenizer, httpx.MockTransport(handle))
    assert completion.text == "not repaired" and completion.input_tokens == 42
    assert seen == ["/api/version", "/api/tags", "/api/generate"]


def test_changed_tag_refuses_generation(tokenizer: Qwen3Tokenizer) -> None:
    paths = []

    def handle(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(
            200,
            json={"version": PINNED_VERSION}
            if request.url.path == "/api/version"
            else {"models": [{"name": MODEL_ID, "digest": "0" * 64}]},
        )

    with pytest.raises(ValueError, match="manifest differs"):
        call_backend(tokenizer, httpx.MockTransport(handle))
    assert "/api/generate" not in paths


def test_changed_server_refused() -> None:
    with pytest.raises(ValueError, match="version differs"):
        check_server({"version": "changed"}, {"models": []})


def test_timeout_becomes_baseline_timeout(tokenizer: Qwen3Tokenizer) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("local timeout", request=request)

    with pytest.raises(TimeoutError):
        call_backend(tokenizer, httpx.MockTransport(handle))


@pytest.mark.parametrize(
    "payload",
    [
        {"model": MODEL_ID, "done": False, "response": "partial", "done_reason": "stop"},
        {"model": "other", "done": True, "response": "{}", "done_reason": "stop"},
        {
            "model": MODEL_ID,
            "done": True,
            "response": "{}",
            "thinking": "unexpected",
            "done_reason": "stop",
        },
        {"model": MODEL_ID, "done": True, "response": "{}", "done_reason": "unexpected"},
    ],
)
def test_response_contract(tokenizer: Qwen3Tokenizer, payload: dict[str, Any]) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": PINNED_VERSION})
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": MODEL_ID, "digest": PINNED_MANIFEST}]}
            )
        return httpx.Response(200, json=payload)

    with pytest.raises(ValueError):
        call_backend(tokenizer, httpx.MockTransport(handle))

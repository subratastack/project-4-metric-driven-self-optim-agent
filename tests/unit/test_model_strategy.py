"""Strategy selection and remote transport checks; never call Ollama or OpenRouter."""

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from conftest import FakeBackend
from conftest import response as decision_response
from pydantic import SecretStr

from apps.decision_program.baseline import Message
from apps.decision_program.model_strategy import (
    GenerationOptions,
    ModelClient,
    OllamaStrategy,
    create_strategy,
)
from apps.decision_program.openrouter_strategy import OpenRouterStrategy, ProviderError
from apps.decision_program.provider_settings import ProviderSettings
from apps.evaluation.dataset import Case

MESSAGES = (Message("system", "Use the contract."), Message("user", "Incident evidence."))
MODEL = "test-vendor/explicit-model"
KEY = "test-secret-never-log"


def settings() -> ProviderSettings:
    return ProviderSettings(
        provider="openrouter", openrouter_model=MODEL, openrouter_api_key=SecretStr(KEY)
    )


def write_env(tmp_path: Path, text: str = "") -> Path:
    path = tmp_path / ".env"
    path.write_text(text)
    return path


def response() -> dict[str, Any]:
    return {
        "id": "generation-test-only",
        "model": MODEL,
        "provider": "test-upstream",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "verbatim, no repair"},
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 7},
    }


def run(transport: httpx.MockTransport) -> Any:
    client = ModelClient(OpenRouterStrategy(settings(), transport=transport))
    return asyncio.run(client.generate(MESSAGES))


def test_default_local_settings_need_no_secrets(tmp_path: Path) -> None:
    result = ProviderSettings.from_env_file(tmp_path / "missing.env")
    assert result.provider == "ollama" and result.ollama_model == "qwen3:14b"
    assert KEY not in repr(settings())


def test_env_file_is_the_only_model_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OPENROUTER_MODEL", "other/model")
    path = write_env(
        tmp_path,
        f"LLM_PROVIDER=openrouter\nOPENROUTER_MODEL={MODEL}\nOPENROUTER_API_KEY={KEY}\n",
    )
    strategy = create_strategy(path)
    assert isinstance(strategy, OpenRouterStrategy)
    assert strategy.identity.model_id == MODEL
    assert strategy.identity.locality == "remote"
    # Selection is a snapshot: edits only take effect when a new strategy is created.
    path.write_text(path.read_text().replace(MODEL, "another/model"))
    assert strategy.identity.model_id == MODEL
    assert create_strategy(path).identity.model_id == "another/model"


def test_shell_model_cannot_fill_missing_file_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", MODEL)
    with pytest.raises(ValueError, match="OPENROUTER_MODEL"):
        create_strategy(write_env(tmp_path, f"LLM_PROVIDER=openrouter\nOPENROUTER_API_KEY={KEY}"))


@pytest.mark.parametrize(
    "model",
    ["", "openrouter/auto", "openrouter/free", "vendor/*", "a/b,c/d", "${MODEL}", "@preset"],
)
def test_missing_or_automatic_models_fail_closed(tmp_path: Path, model: str) -> None:
    path = write_env(
        tmp_path,
        f"LLM_PROVIDER=openrouter\nOPENROUTER_MODEL={model}\nOPENROUTER_API_KEY={KEY}",
    )
    with pytest.raises(ValueError):
        create_strategy(path)


@pytest.mark.parametrize(
    "text",
    [
        "LLM_PROVIDER=unknown",
        "LLM_PROVIDER=",
        "LLM_PROVIDER=openrouter\nOPENROUTER_MODEL=vendor/model",
        "OLLAMA_MODEL=unapproved-model",
        "OLLAMA_BASE_URL=https://remote.example",
    ],
)
def test_invalid_selected_provider_settings(tmp_path: Path, text: str) -> None:
    with pytest.raises(ValueError):
        create_strategy(write_env(tmp_path, text))


def test_ollama_selection_reuses_existing_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = FakeBackend("local output")
    monkeypatch.setattr("apps.decision_program.model_strategy.create_backend", lambda: backend)
    client = ModelClient.from_env_file(write_env(tmp_path, "LLM_PROVIDER=ollama"))
    result = asyncio.run(client.generate(MESSAGES))
    assert client.identity.provider == "ollama"
    assert result.completion.text == "local output"
    assert result.preflight_input_tokens == 100
    assert len(backend.calls) == 1
    assert backend.calls[0]["temperature"] == 0.0


def test_remote_request_has_only_configured_model_and_no_fallback() -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer " + KEY
        assert json.loads(request.content) == {
            "model": MODEL,
            "messages": [{"role": m.role, "content": m.content} for m in MESSAGES],
            "stream": False,
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 101,
            "max_tokens": 512,
            "provider": {"allow_fallbacks": False, "require_parameters": True},
            "transforms": [],
        }
        return httpx.Response(200, json=response())

    result = run(httpx.MockTransport(handle))
    assert len(requests) == 1
    assert result.completion.text == "verbatim, no repair"
    assert result.completion.input_tokens == 100
    assert result.completion.output_tokens == 7
    assert result.preflight_input_tokens is None
    assert result.response_id == "generation-test-only"
    assert result.upstream_provider == "test-upstream"


@pytest.mark.parametrize("status", [302, 401, 402, 429, 500, 503])
def test_http_errors_are_not_retried_or_leaked(status: int) -> None:
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            status, text=KEY + " sensitive evidence", headers={"location": "https://other.example"}
        )

    with pytest.raises(ProviderError) as caught:
        run(httpx.MockTransport(handle))
    assert str(caught.value) == f"OpenRouter HTTP {status}"
    assert len(calls) == 1


@pytest.mark.parametrize("timeout", [True, False])
def test_transport_failures_are_sanitized(timeout: bool) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if timeout:
            raise httpx.ReadTimeout(KEY, request=request)
        raise httpx.ConnectError(KEY, request=request)

    with pytest.raises(TimeoutError if timeout else ProviderError) as caught:
        run(httpx.MockTransport(handle))
    assert KEY not in str(caught.value)


@pytest.mark.parametrize(
    "update",
    [
        {"model": "different/model"},
        {"error": {"message": KEY}},
        {"choices": []},
        {"choices": [{"finish_reason": "tool_calls", "message": {"content": None}}]},
        {"usage": {"prompt_tokens": True}},
        {"usage": {"completion_tokens": -1}},
        {"usage": {"completion_tokens": 1.5}},
        {"id": 42},
        {"provider": {}},
    ],
)
def test_unexpected_response_rejected(update: dict[str, Any]) -> None:
    data = response() | update
    with pytest.raises(ProviderError, match="invalid or unexpected"):
        run(httpx.MockTransport(lambda _: httpx.Response(200, json=data)))


@pytest.mark.parametrize("finish", ["stop", "length"])
def test_unknown_usage_remains_unknown_and_truncation_is_retained(finish: str) -> None:
    data = response()
    data.pop("usage")
    data["choices"][0]["finish_reason"] = finish
    result = run(httpx.MockTransport(lambda _: httpx.Response(200, json=data)))
    assert result.completion.input_tokens is None and result.completion.output_tokens is None
    assert result.completion.finish_reason == finish


def test_local_preflight_prevents_overflow() -> None:
    backend = FakeBackend("unused", count=8193)
    with pytest.raises(ValueError, match="input exceeds"):
        asyncio.run(ModelClient(OllamaStrategy(backend)).generate(MESSAGES))
    assert not backend.calls


def test_context_has_an_overall_deadline() -> None:
    backend = FakeBackend("unused", delay=0.1)
    with pytest.raises(TimeoutError):
        asyncio.run(
            ModelClient(OllamaStrategy(backend)).generate(MESSAGES, GenerationOptions(timeout_ms=5))
        )


@pytest.mark.parametrize("kwargs", [{"max_output_tokens": 513}, {"timeout_ms": 0}, {"seed": True}])
def test_generation_options_are_bounded(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        GenerationOptions(**kwargs)


def test_config_check_does_not_call_providers_or_print_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts.run_model import main

    path = write_env(
        tmp_path,
        f"LLM_PROVIDER=openrouter\nOPENROUTER_MODEL={MODEL}\nOPENROUTER_API_KEY={KEY}",
    )
    monkeypatch.setattr("sys.argv", ["run_model", "--check", "--env-file", str(path)])
    main()
    printed = capsys.readouterr().out
    assert json.loads(printed) == {"provider": "openrouter", "model": MODEL}
    assert KEY not in printed


@pytest.mark.parametrize("field", ["tool_calls", "function_call", "refusal"])
def test_tool_or_refusal_responses_are_not_text_decisions(field: str) -> None:
    data = response()
    data["choices"][0]["message"][field] = [{"unexpected": True}]
    with pytest.raises(ProviderError):
        run(httpx.MockTransport(lambda _: httpx.Response(200, json=data)))


def test_non_json_response_is_sanitized() -> None:
    with pytest.raises(ProviderError) as caught:
        run(httpx.MockTransport(lambda _: httpx.Response(200, text=KEY)))
    assert KEY not in str(caught.value)


def test_remote_output_overrun_rejected() -> None:
    data = response()
    data["usage"]["completion_tokens"] = 513
    with pytest.raises(ValueError, match="output allocation"):
        run(httpx.MockTransport(lambda _: httpx.Response(200, json=data)))


def test_local_tokenizer_mismatch_rejected() -> None:
    from apps.decision_program.baseline import Completion

    backend = FakeBackend("text")
    backend.completion = Completion("text", 99, 1, "stop")
    with pytest.raises(ValueError, match="tokenizer/usage mismatch"):
        asyncio.run(ModelClient(OllamaStrategy(backend)).generate(MESSAGES))


@pytest.mark.parametrize("provider", ["ollama", "openrouter"])
def test_same_incident_renderer_and_parser_work_with_both_strategies(
    provider: str, case: Case
) -> None:
    from apps.decision_program.baseline import render_request
    from apps.decision_program.signature import parse_decision

    raw = decision_response(case)
    if provider == "ollama":
        client = ModelClient(OllamaStrategy(FakeBackend(raw)))
    else:
        data = response()
        data["choices"][0]["message"]["content"] = raw
        client = ModelClient(
            OpenRouterStrategy(
                settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=data))
            )
        )
    result = asyncio.run(client.generate(render_request(case.input)))
    decision = parse_decision(result.completion.text, case.input)
    assert decision.request_id == case.input.request_id


def test_cli_invocation_uses_selected_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts.run_model import main

    env = write_env(tmp_path, "LLM_PROVIDER=ollama")
    messages = tmp_path / "messages.json"
    messages.write_text(json.dumps([{"role": m.role, "content": m.content} for m in MESSAGES]))
    backend = FakeBackend("local result")
    monkeypatch.setattr("apps.decision_program.model_strategy.create_backend", lambda: backend)
    monkeypatch.setattr(
        "sys.argv", ["run_model", "--env-file", str(env), "--messages", str(messages)]
    )
    main()
    output = json.loads(capsys.readouterr().out)
    assert output["identity"]["provider"] == "ollama"
    assert output["completion"]["text"] == "local result"
    assert len(backend.calls) == 1

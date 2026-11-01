"""Pinned local Qwen3 adapter: no downloads, remote endpoints, tools, retries or repair."""

from __future__ import annotations

import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

import httpx

from apps.decision_program.baseline import Completion, Message
from apps.decision_program.qwen3_tokenizer import Qwen3Tokenizer, metadata_bytes, render_chat
from apps.decision_program.signature import sha256
from apps.decision_program.versions import ModelBinding

MODEL_ID = "qwen3:14b"
BASE_URL = "http://127.0.0.1:11434"
PINNED_MANIFEST = "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8"
PINNED_WEIGHTS = "a8cc1361f3145dc01f6d77c6c82c9116b9ffe3c97b34716fe20418455876c40e"
PINNED_LICENSE = "d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12"
PINNED_VERSION = "0.20.0"
CONTEXT_TOKENS = 8704


def adapter_digest() -> str:
    root = Path(__file__).parent
    return sha256(
        metadata_bytes(
            {
                "files": {
                    name: sha256((root / name).read_bytes())
                    for name in ("ollama_backend.py", "qwen3_tokenizer.py")
                },
                "httpx_version": version("httpx"),
                "tokenizers_version": version("tokenizers"),
            }
        )
    )


def check_server(version_info: Any, tags: Any) -> None:
    if version_info.get("version") != PINNED_VERSION:
        raise ValueError("Ollama version differs from the frozen binding")
    matches = [m for m in tags.get("models", []) if m.get("name") == MODEL_ID]
    if len(matches) != 1 or matches[0].get("digest") != PINNED_MANIFEST:
        raise ValueError("qwen3:14b manifest differs from the frozen binding")


class OllamaQwen3Backend:
    def __init__(
        self, tokenizer: Qwen3Tokenizer, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.tokenizer = tokenizer
        self._transport = transport
        self.identity = ModelBinding.model_validate(
            {
                "model_id": MODEL_ID,
                "weights_sha256": PINNED_WEIGHTS,
                "tokenizer_sha256": tokenizer.identity_sha256,
                "backend": "ollama-raw-generate",
                "backend_version": PINNED_VERSION,
                "backend_adapter_sha256": adapter_digest(),
                "license_ref": "Apache-2.0; installed-license-sha256:" + PINNED_LICENSE,
                "context_tokens": CONTEXT_TOKENS,
                "seed_supported": True,
                "locality": "local",
            }
        )

    async def count_input_tokens(self, messages: tuple[Message, ...]) -> int:
        return self.tokenizer.count(messages)

    async def generate(
        self,
        messages: tuple[Message, ...],
        *,
        seed: int,
        temperature: float,
        top_p: float,
        max_output_tokens: int,
        timeout_ms: int,
    ) -> Completion:
        if adapter_digest() != self.identity.backend_adapter_sha256:
            raise ValueError("adapter changed after binding")
        if (
            type(seed) is not int
            or temperature != 0.0
            or top_p != 1.0
            or not 1 <= max_output_tokens <= 512
            or not 1 <= timeout_ms <= 30000
        ):
            raise ValueError("generation settings exceed the frozen profile")
        if self.tokenizer.count(messages) > 8192:
            raise ValueError("input exceeds frozen context allocation")
        try:
            async with httpx.AsyncClient(
                base_url=BASE_URL,
                trust_env=False,
                follow_redirects=False,
                timeout=timeout_ms / 1000,
                transport=self._transport,
            ) as client:
                version_response = await client.get("/api/version")
                tags_response = await client.get("/api/tags")
                version_response.raise_for_status()
                tags_response.raise_for_status()
                check_server(version_response.json(), tags_response.json())
                result = await client.post(
                    "/api/generate",
                    json={
                        "model": MODEL_ID,
                        "prompt": render_chat(messages),
                        "raw": True,
                        "stream": False,
                        "think": False,
                        "keep_alive": "5m",
                        "options": {
                            "seed": seed,
                            "temperature": temperature,
                            "top_p": top_p,
                            "top_k": 0,
                            "min_p": 0.0,
                            "repeat_penalty": 1.0,
                            "num_ctx": CONTEXT_TOKENS,
                            "num_predict": max_output_tokens,
                            "stop": ["<|im_start|>", "<|im_end|>"],
                        },
                    },
                )
                result.raise_for_status()
                data = result.json()
        except httpx.TimeoutException as error:
            raise TimeoutError("local generation deadline") from error
        if data.get("model") != MODEL_ID or data.get("done") is not True or data.get("thinking"):
            raise ValueError("unexpected model response identity, completion or thinking output")
        if not isinstance(data.get("response"), str) or data.get("done_reason") not in (
            "stop",
            "length",
        ):
            raise ValueError("malformed Ollama completion")
        return Completion(
            data["response"],
            data.get("prompt_eval_count"),
            data.get("eval_count"),
            data["done_reason"],
        )


def create_backend() -> OllamaQwen3Backend:
    """Verify existing blobs and local server metadata; never pull/create a model."""
    root = Path.home() / ".ollama/models"
    manifest_path = root / "manifests/registry.ollama.ai/library/qwen3/14b"
    raw_manifest = manifest_path.read_bytes()
    if sha256(raw_manifest) != PINNED_MANIFEST:
        raise ValueError("installed model manifest does not match the selected qwen3:14b")
    manifest = json.loads(raw_manifest)
    for layer in [manifest["config"], *manifest["layers"]]:
        digest = layer["digest"].removeprefix("sha256:")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid model blob reference")
        path = root / "blobs" / ("sha256-" + digest)
        if path.stat().st_size != layer["size"]:
            raise ValueError("model blob size mismatch")
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError("model blob content digest mismatch")
    with httpx.Client(
        base_url=BASE_URL, trust_env=False, follow_redirects=False, timeout=10
    ) as client:
        version_response = client.get("/api/version")
        tags_response = client.get("/api/tags")
        version_response.raise_for_status()
        tags_response.raise_for_status()
        check_server(version_response.json(), tags_response.json())
        response = client.post("/api/show", json={"model": MODEL_ID, "verbose": True})
        response.raise_for_status()
        shown = response.json()
    if sha256(shown["license"].encode()) != PINNED_LICENSE:
        raise ValueError("served license differs from the pinned installed license")
    info = shown["model_info"]
    if (
        info.get("general.architecture") != "qwen3"
        or info.get("qwen3.context_length", 0) < CONTEXT_TOKENS
    ):
        raise ValueError("unsupported model architecture/context")
    return OllamaQwen3Backend(Qwen3Tokenizer(info))

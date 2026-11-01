"""Provider Strategy interface and context, separate from the immutable local baseline."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from apps.decision_program.baseline import Completion, LocalBackend, Message
from apps.decision_program.ollama_backend import create_backend
from apps.decision_program.provider_settings import ProviderSettings
from apps.decision_program.versions import INPUT_LIMIT, PROJECT_ROOT


@dataclass(frozen=True)
class GenerationOptions:
    seed: int = 101
    max_output_tokens: int = 512
    timeout_ms: int = 30000

    def __post_init__(self) -> None:
        if type(self.seed) is not int or not 0 <= self.seed <= 2147483647:
            raise ValueError("seed must be an integer between 0 and 2147483647")
        if type(self.max_output_tokens) is not int or not 1 <= self.max_output_tokens <= 512:
            raise ValueError("max_output_tokens must be between 1 and 512")
        if type(self.timeout_ms) is not int or not 1 <= self.timeout_ms <= 30000:
            raise ValueError("timeout_ms must be between 1 and 30000")


@dataclass(frozen=True)
class ProviderIdentity:
    provider: Literal["ollama", "openrouter"]
    model_id: str
    locality: Literal["local", "remote"]


@dataclass(frozen=True)
class ModelResponse:
    identity: ProviderIdentity
    completion: Completion
    preflight_input_tokens: int | None
    response_id: str | None = None
    upstream_provider: str | None = None


class ModelStrategy(Protocol):
    @property
    def identity(self) -> ProviderIdentity: ...

    async def count_input_tokens(self, messages: tuple[Message, ...]) -> int | None:
        """Exact local count, or None when the provider has no bound local tokenizer."""
        ...

    async def generate(
        self, messages: tuple[Message, ...], options: GenerationOptions
    ) -> ModelResponse: ...


class OllamaStrategy:
    """Delegate to the existing verified adapter, retaining its model and tokenizer checks."""

    def __init__(self, backend: LocalBackend) -> None:
        self._backend = backend
        self._binding = backend.identity
        self._identity = ProviderIdentity("ollama", self._binding.model_id, "local")

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    async def count_input_tokens(self, messages: tuple[Message, ...]) -> int:
        return await self._backend.count_input_tokens(messages)

    async def generate(
        self, messages: tuple[Message, ...], options: GenerationOptions
    ) -> ModelResponse:
        if self._backend.identity != self._binding:
            raise ValueError("Ollama model binding changed after strategy selection")
        completion = await self._backend.generate(
            messages,
            seed=options.seed,
            temperature=0.0,
            top_p=1.0,
            max_output_tokens=options.max_output_tokens,
            timeout_ms=options.timeout_ms,
        )
        return ModelResponse(self.identity, completion, None)


def create_strategy(env_file: Path = PROJECT_ROOT / ".env") -> ModelStrategy:
    """Select one strategy once; no network activity for OpenRouter until generate()."""
    settings = ProviderSettings.from_env_file(env_file)
    if settings.provider == "ollama":
        return OllamaStrategy(create_backend())
    from apps.decision_program.openrouter_strategy import OpenRouterStrategy

    return OpenRouterStrategy(settings)


class ModelClient:
    """Context for interchangeable providers. This is not a frozen benchmark execution."""

    def __init__(self, strategy: ModelStrategy) -> None:
        self._strategy = strategy

    @classmethod
    def from_env_file(cls, path: Path = PROJECT_ROOT / ".env") -> ModelClient:
        return cls(create_strategy(path))

    @property
    def identity(self) -> ProviderIdentity:
        return self._strategy.identity

    async def generate(
        self, messages: tuple[Message, ...], options: GenerationOptions | None = None
    ) -> ModelResponse:
        options = options or GenerationOptions()
        identity = self.identity
        if (
            len(messages) != 2
            or tuple(message.role for message in messages) != ("system", "user")
            or any(not isinstance(message.content, str) for message in messages)
        ):
            raise ValueError("supply exactly one system message and one user message")
        async with asyncio.timeout(options.timeout_ms / 1000):
            count = await self._strategy.count_input_tokens(messages)
            if count is not None and (type(count) is not int or not 1 <= count <= INPUT_LIMIT):
                raise ValueError("input exceeds the local token allocation or count is invalid")
            response = await self._strategy.generate(messages, options)
        if response.identity != identity or self.identity != identity:
            raise ValueError("provider identity changed during generation")
        completion = response.completion
        if not isinstance(completion.text, str) or completion.finish_reason not in (
            "stop",
            "length",
        ):
            raise ValueError("invalid provider text completion")
        completion.text.encode("utf-8", errors="strict")
        for used in (completion.input_tokens, completion.output_tokens):
            if used is not None and (type(used) is not int or used < 0):
                raise ValueError("invalid provider usage")
        if (
            count is not None
            and completion.input_tokens is not None
            and count != completion.input_tokens
        ):
            raise ValueError("local tokenizer/usage mismatch")
        if (
            completion.output_tokens is not None
            and completion.output_tokens > options.max_output_tokens
        ):
            raise ValueError("provider exceeded the requested output allocation")
        return ModelResponse(
            response.identity, completion, count, response.response_id, response.upstream_provider
        )

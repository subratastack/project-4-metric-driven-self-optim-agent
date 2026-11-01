"""One explicit .env-selected model, one HTTPS call, no fallback or output repair."""

from __future__ import annotations

from typing import Any

import httpx

from apps.decision_program.baseline import Completion, Message
from apps.decision_program.model_strategy import GenerationOptions, ModelResponse, ProviderIdentity
from apps.decision_program.provider_settings import ProviderSettings

BASE_URL = "https://openrouter.ai/api/v1"


class ProviderError(RuntimeError):
    """Safe error text: excludes provider bodies, credentials and request contents."""


class OpenRouterStrategy:
    def __init__(
        self, settings: ProviderSettings, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        if settings.provider != "openrouter":
            raise ValueError("OpenRouter strategy requires OpenRouter settings")
        self._settings = settings
        self._transport = transport
        self._identity = ProviderIdentity("openrouter", settings.openrouter_model, "remote")

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    async def count_input_tokens(self, messages: tuple[Message, ...]) -> None:
        # Do not manufacture exact counts from a tokenizer for a different model.
        return None

    async def generate(
        self, messages: tuple[Message, ...], options: GenerationOptions
    ) -> ModelResponse:
        try:
            async with httpx.AsyncClient(
                base_url=BASE_URL + "/",
                headers={
                    "Authorization": "Bearer "
                    + self._settings.openrouter_api_key.get_secret_value()
                },
                trust_env=False,
                follow_redirects=False,
                timeout=options.timeout_ms / 1000,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    "chat/completions",
                    json={
                        "model": self._settings.openrouter_model,
                        "messages": [
                            {"role": message.role, "content": message.content}
                            for message in messages
                        ],
                        "stream": False,
                        "temperature": 0.0,
                        "top_p": 1.0,
                        "seed": options.seed,
                        "max_tokens": options.max_output_tokens,
                        "provider": {"allow_fallbacks": False, "require_parameters": True},
                        "transforms": [],
                    },
                )
        except httpx.TimeoutException:
            raise TimeoutError("OpenRouter request timed out") from None
        except httpx.RequestError:
            raise ProviderError("OpenRouter transport failed") from None
        if response.status_code != 200:
            raise ProviderError(f"OpenRouter HTTP {response.status_code}")
        try:
            return self._parse(response.json())
        except (ValueError, KeyError, TypeError, IndexError, AttributeError):
            raise ProviderError("OpenRouter returned an invalid or unexpected completion") from None

    def _parse(self, data: Any) -> ModelResponse:
        if "error" in data or data["model"] != self._settings.openrouter_model:
            raise ValueError("model mismatch or provider error")
        choices = data["choices"]
        if not isinstance(choices, list) or len(choices) != 1:
            raise ValueError("expected one completion")
        choice = choices[0]
        message = choice["message"]
        if (
            message.get("role") != "assistant"
            or not isinstance(message["content"], str)
            or message.get("tool_calls")
            or message.get("function_call")
            or message.get("refusal")
            or choice["finish_reason"] not in ("stop", "length")
        ):
            raise ValueError("expected a text completion without tool calls")
        usage = data.get("usage") or {}
        counts = (usage.get("prompt_tokens"), usage.get("completion_tokens"))
        for count in counts:
            if count is not None and (type(count) is not int or count < 0):
                raise ValueError("invalid measured usage")
        response_id, upstream = data.get("id"), data.get("provider")
        if any(
            value is not None and not isinstance(value, str) for value in (response_id, upstream)
        ):
            raise ValueError("invalid completion metadata")
        return ModelResponse(
            self.identity,
            Completion(message["content"], *counts, choice["finish_reason"]),
            None,
            response_id,
            upstream,
        )

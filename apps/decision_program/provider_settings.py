"""File-only provider selection; process environment cannot replace the selected model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import SecretStr

from apps.decision_program.ollama_backend import BASE_URL, MODEL_ID
from apps.decision_program.versions import PROJECT_ROOT


@dataclass(frozen=True)
class ProviderSettings:
    provider: Literal["ollama", "openrouter"] = "ollama"
    ollama_model: str = MODEL_ID
    ollama_base_url: str = BASE_URL
    openrouter_model: str = ""
    openrouter_api_key: SecretStr = field(default_factory=lambda: SecretStr(""), repr=False)

    def __post_init__(self) -> None:
        if self.provider == "ollama":
            if self.ollama_model != MODEL_ID or self.ollama_base_url != BASE_URL:
                raise ValueError(
                    "Ollama currently supports only the verified local qwen3:14b binding"
                )
        elif self.provider == "openrouter":
            # A concrete model slug, never a router, preset, list or expression.
            if not re.fullmatch(r"[\w.-]+/[\w.-]+(?::[\w.-]+)?", self.openrouter_model, re.ASCII):
                raise ValueError("Set OPENROUTER_MODEL to one explicit vendor/model slug in .env")
            if self.openrouter_model.split("/")[0].lower() == "openrouter":
                raise ValueError("OpenRouter automatic model routers are not allowed")
            key = self.openrouter_api_key.get_secret_value()
            if not key or any(char.isspace() or ord(char) < 33 or ord(char) > 126 for char in key):
                raise ValueError("Set OPENROUTER_API_KEY in .env to a valid API key")
        else:
            raise ValueError("LLM_PROVIDER must be ollama or openrouter")

    @classmethod
    def from_env_file(cls, path: Path = PROJECT_ROOT / ".env") -> ProviderSettings:
        """Read only the named file. No shell overrides, interpolation or parent-file search."""
        values = dotenv_values(path, interpolate=False) if path.is_file() else {}
        provider = values.get("LLM_PROVIDER", "ollama")
        if provider not in ("ollama", "openrouter"):
            raise ValueError("LLM_PROVIDER must be ollama or openrouter")
        return cls(
            provider="ollama" if provider == "ollama" else "openrouter",
            ollama_model=values.get("OLLAMA_MODEL") or MODEL_ID,
            ollama_base_url=values.get("OLLAMA_BASE_URL") or BASE_URL,
            openrouter_model=values.get("OPENROUTER_MODEL") or "",
            openrouter_api_key=SecretStr(values.get("OPENROUTER_API_KEY") or ""),
        )

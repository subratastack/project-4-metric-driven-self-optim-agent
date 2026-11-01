"""Invoke the configured provider with two messages, or inspect configuration without inference."""

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from apps.decision_program.baseline import Message
from apps.decision_program.model_strategy import ModelClient
from apps.decision_program.openrouter_strategy import ProviderError
from apps.decision_program.provider_settings import ProviderSettings
from apps.decision_program.signature import load_json
from apps.decision_program.versions import PROJECT_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=PROJECT_ROOT / ".env")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="No network requests or model loading")
    mode.add_argument("--messages", type=Path, help="JSON array with system and user messages")
    args = parser.parse_args()
    try:
        settings = ProviderSettings.from_env_file(args.env_file)
        if args.check:
            model = (
                settings.ollama_model
                if settings.provider == "ollama"
                else settings.openrouter_model
            )
            print(json.dumps({"provider": settings.provider, "model": model}))
            return
        payload = load_json(args.messages.read_bytes())
        if not isinstance(payload, list) or len(payload) != 2:
            raise ValueError("messages file must contain one system and one user message")
        messages = []
        for item in payload:
            if not isinstance(item, dict) or set(item) != {"role", "content"}:
                raise ValueError("each message must contain only role and content")
            if item["role"] not in ("system", "user") or not isinstance(item["content"], str):
                raise ValueError("invalid message role or content")
            messages.append(Message(item["role"], item["content"]))
        if tuple(item.role for item in messages) != ("system", "user"):
            raise ValueError("supply system then user messages")
        client = ModelClient.from_env_file(args.env_file)
        result = asyncio.run(client.generate(tuple(messages)))
    except (ValueError, OSError, ProviderError, TimeoutError) as error:
        parser.error(str(error))
    print(json.dumps(asdict(result), ensure_ascii=False))


if __name__ == "__main__":
    main()

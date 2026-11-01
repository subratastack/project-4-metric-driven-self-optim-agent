"""Qwen3 byte-pair tokenization reconstructed from the installed GGUF metadata.

No pretrained tokenizer is downloaded. This supports only the declared qwen2
pre-tokenizer used by the pinned Qwen3 GGUF, and rejects other tokenizer profiles.
"""

import json
from importlib.metadata import version
from typing import Any

from tokenizers import AddedToken, Regex, Tokenizer, models, pre_tokenizers

from apps.decision_program.baseline import Message
from apps.decision_program.signature import sha256

# Ollama v0.20.0 qwen2 BPE expression; see docs/qwen3-local-verification.md.
PATTERN = (
    r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}|"
    r" ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
)
TEMPLATE_ID = "qwen3-two-message-no-thinking-v1"
TEMPLATE = (
    "<|im_start|>system\n{system}<|im_end|>\n"
    "<|im_start|>user\n{user} /no_think<|im_end|>\n"
    "<|im_start|>assistant\n<think>\n\n</think>\n\n"
)


def metadata_bytes(value: Any) -> bytes:
    """Hash metadata verbatim; vocabulary text must never be Unicode-normalized."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def render_chat(messages: tuple[Message, ...]) -> str:
    if len(messages) != 2 or [m.role for m in messages] != ["system", "user"]:
        raise ValueError("Qwen3 adapter accepts exactly one system and one user message")
    return TEMPLATE.format(system=messages[0].content, user=messages[1].content)


class Qwen3Tokenizer:
    def __init__(self, model_info: dict[str, Any]) -> None:
        info = {k: v for k, v in model_info.items() if k.startswith("tokenizer.")}
        if (
            info.get("tokenizer.ggml.model") != "gpt2"
            or info.get("tokenizer.ggml.pre") != "qwen2"
            or info.get("tokenizer.ggml.add_bos_token") is not False
            or info.get("tokenizer.ggml.add_eos_token", False) is not False
        ):
            raise ValueError("unsupported tokenizer profile")
        tokens = info["tokenizer.ggml.tokens"]
        types = info["tokenizer.ggml.token_type"]
        merges = [tuple(m.split(" ")) for m in info["tokenizer.ggml.merges"]]
        if len(tokens) != len(types) or len(set(tokens)) != len(tokens):
            raise ValueError("invalid GGUF token vocabulary")
        if any(len(m) != 2 for m in merges) or any(kind not in (1, 3, 4, 5) for kind in types):
            raise ValueError("unsupported GGUF merges or token types")
        vocab = {token: i for i, token in enumerate(tokens)}
        tokenizer = Tokenizer(models.BPE(vocab, merges))
        tokenizer.pre_tokenizer = pre_tokenizers.Sequence(
            [
                pre_tokenizers.Split(Regex(PATTERN), behavior="isolated"),
                pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False),
            ]
        )
        specials = [token for token, kind in zip(tokens, types, strict=True) if kind in (3, 4)]
        tokenizer.add_special_tokens(
            [AddedToken(token, special=True, normalized=False) for token in specials]
        )
        for token in specials:
            if tokenizer.encode(token, add_special_tokens=False).ids != [vocab[token]]:
                raise ValueError("special token identity mismatch")
        self._tokenizer = tokenizer
        self.metadata_sha256 = sha256(metadata_bytes(info))
        self.identity_sha256 = sha256(
            metadata_bytes(
                {
                    "metadata_sha256": self.metadata_sha256,
                    "pattern": PATTERN,
                    "tokenizers_version": version("tokenizers"),
                    "template_id": TEMPLATE_ID,
                    "template": TEMPLATE,
                    "add_special_tokens": False,
                }
            )
        )

    def encode(self, text: str) -> list[int]:
        return list(self._tokenizer.encode(text, add_special_tokens=False).ids)

    def count(self, messages: tuple[Message, ...]) -> int:
        return len(self.encode(render_chat(messages)))

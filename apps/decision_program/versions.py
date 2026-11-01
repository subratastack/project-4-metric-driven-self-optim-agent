"""Content-addressed implementation freeze and explicit local model binding."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from apps.decision_program.signature import Contract, Digest, canonical_json, load_json, sha256

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROGRAM_ID = "frozen-baseline-v1"
SEEDS = (101, 202, 303, 404, 505)
INPUT_LIMIT = 8192
OUTPUT_LIMIT = 512
DEADLINE_MS = 30000
FREEZE_PATH = PROJECT_ROOT / "apps/decision_program/baseline.freeze.json"
FROZEN_FILES = (
    "apps/__init__.py",
    "apps/decision_program/__init__.py",
    "apps/evaluation/__init__.py",
    "apps/evaluation/metrics/__init__.py",
    "apps/decision_program/baseline.py",
    "apps/decision_program/versions.py",
    "apps/decision_program/signature.py",
    "apps/decision_program/tool_catalog.py",
    "apps/decision_program/prompts/baseline-v1.txt",
    "apps/decision_program/prompts/envelope-v1.txt",
    "apps/decision_program/prompts/output-contract-v1.json",
    "apps/evaluation/metrics/tool_policy.py",
    "uv.lock",
)


class ModelBinding(Contract):
    """Actual backend identity, supplied only after model/license/tokenizer selection."""

    model_id: Annotated[str, Field(min_length=1)]
    weights_sha256: Digest
    tokenizer_sha256: Digest
    backend: Annotated[str, Field(min_length=1)]
    backend_version: Annotated[str, Field(min_length=1)]
    backend_adapter_sha256: Digest
    license_ref: Annotated[str, Field(min_length=1)]
    context_tokens: Annotated[int, Field(ge=INPUT_LIMIT + OUTPUT_LIMIT)]
    seed_supported: bool
    locality: Literal["local"]


def freeze_payload(root: Path = PROJECT_ROOT) -> dict[str, object]:
    return {
        "schema_version": "baseline-implementation/v1",
        "program_id": PROGRAM_ID,
        "model_binding": None,
        "execution_release": False,
        "decision_contract": "action-decision/v1",
        "prompt_id": "baseline-prompt/v1",
        "tool_catalog_version": "incident-tools-v1",
        "runtime_policy_version": "runtime-policy-v1",
        "profile": {
            "temperature": "0.0",
            "top_p": "1.0",
            "seeds": list(SEEDS),
            "input_limit": INPUT_LIMIT,
            "output_limit": OUTPUT_LIMIT,
            "deadline_ms": DEADLINE_MS,
            "demonstrations": 0,
            "model_calls_per_attempt": 1,
            "retries": 0,
            "json_repairs": 0,
        },
        "files": {name: sha256((root / name).read_bytes()) for name in FROZEN_FILES},
    }


def verify_freeze(root: Path = PROJECT_ROOT) -> str:
    path = root / FREEZE_PATH.relative_to(PROJECT_ROOT)
    raw = path.read_bytes()
    data = load_json(raw)
    if raw != canonical_json(data) + b"\n" or data != freeze_payload(root):
        raise ValueError("frozen baseline artifact mismatch; create a new reviewed version")
    return sha256(raw)


def execution_identity(binding: ModelBinding, implementation_digest: str) -> str:
    """A model change creates a different identity, never silently replacing the baseline."""
    return sha256(
        canonical_json({"implementation": implementation_digest, "model": binding.model_dump()})
    )

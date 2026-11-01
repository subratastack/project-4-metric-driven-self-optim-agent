"""Synthetic backend fixtures exercise the harness; they are not benchmark evidence."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from apps.decision_program.baseline import Completion, Message
from apps.decision_program.signature import canonical_json
from apps.decision_program.versions import PROJECT_ROOT, ModelBinding
from apps.evaluation.dataset import Case, Dataset, load_dataset

DATASET_ROOT = PROJECT_ROOT / "datasets"
MANIFEST = DATASET_ROOT / "manifests/incident-decisions-draft-v1.json"


def corpus() -> Dataset:
    return load_dataset(DATASET_ROOT, MANIFEST, allow_draft=True)


@pytest.fixture(scope="session")
def dataset() -> Dataset:
    return corpus()


@pytest.fixture
def case(dataset: Dataset) -> Case:
    return next(
        c
        for c in dataset.cases
        if c.provenance.source_ref == "project-4:scenario:checkout-leaked-transactions"
        and "initial" in c.tags
    )


def response(case: Case, **updates: Any) -> str:
    data = {
        "schema_version": "action-decision/v1",
        "request_id": case.input.request_id,
        **case.expectations.acceptable_decisions[0].model_dump(),
        "evidence_ids": case.expectations.required_evidence_sets[0],
        "reason": "Fixture response.",
    }
    data.update(updates)
    return canonical_json(data).decode()


class FakeBackend:
    """Test-only adapter. Arbitrary fixture token counts must never be reported as LM usage."""

    def __init__(
        self, raw: str, *, count: int = 100, delay: float = 0, failure: Exception | None = None
    ) -> None:
        self.identity = ModelBinding.model_validate(
            {
                "model_id": "test-double-only",
                "weights_sha256": "0" * 64,
                "tokenizer_sha256": "1" * 64,
                "backend": "pytest-fixture",
                "backend_version": "1",
                "backend_adapter_sha256": "2" * 64,
                "license_ref": "synthetic-test-fixture",
                "context_tokens": 8704,
                "seed_supported": False,
                "locality": "local",
            }
        )
        self.completion = Completion(raw, count, 30, "stop")
        self.count = count
        self.delay = delay
        self.failure = failure
        self.calls: list[dict[str, Any]] = []
        self.counts = 0

    async def count_input_tokens(self, messages: tuple[Message, ...]) -> int:
        self.counts += 1
        return self.count

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
        self.calls.append(
            {
                "messages": messages,
                "seed": seed,
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_output_tokens,
                "timeout_ms": timeout_ms,
            }
        )
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.failure:
            raise self.failure
        return self.completion


@pytest.fixture
def copied_dataset(tmp_path: Path) -> Path:
    from scripts.build_dataset import build_artifacts

    for name, blob in build_artifacts().items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    return tmp_path

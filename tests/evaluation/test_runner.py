"""Exercise persisted evaluation accounting end-to-end using test-only model responses."""

import asyncio
import json
from pathlib import Path

import pytest
from conftest import FakeBackend, response

from apps.decision_program.baseline import Completion, FrozenBaseline, Message
from apps.decision_program.signature import canonical_json
from apps.decision_program.versions import SEEDS
from apps.evaluation.dataset import Case, Dataset
from apps.evaluation.runner import evaluate


class AbstainBackend(FakeBackend):
    """Test adapter with no labels; all token counts here are synthetic fixture values."""

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
        await super().generate(
            messages,
            seed=seed,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            timeout_ms=timeout_ms,
        )
        value = json.loads(messages[1].content)
        assert set(value) == {"request", "output_contract"}
        return Completion(
            canonical_json(
                {
                    "schema_version": "action-decision/v1",
                    "request_id": value["request"]["request_id"],
                    "kind": "abstain",
                    "action_id": None,
                    "hypothesis_id": None,
                    "evidence_ids": [],
                    "reason": "Test double.",
                }
            ).decode(),
            100,
            30,
            "stop",
        )


def test_complete_run_artifacts(dataset: Dataset, tmp_path: Path) -> None:
    backend = AbstainBackend("unused")
    destination = asyncio.run(
        evaluate(dataset, "train", FrozenBaseline(backend), tmp_path, allow_draft=True)
    )
    metadata = json.loads((destination / "run.json").read_text())
    summary = json.loads((destination / "summary.json").read_text())
    rows = [
        json.loads(line) for line in (destination / "observations.jsonl").read_text().splitlines()
    ]
    assert len(rows) == len(backend.calls) == 200
    assert summary["complete"] and summary["observed_count"] == summary["scheduled_count"] == 200
    assert metadata["seed_schedule"] == list(SEEDS)
    assert metadata["draft"] and metadata["budget"]["optimizer_model_calls"] == 0
    assert metadata["manifest_sha256"] == dataset.manifest_sha256
    assert summary["metrics"]["schema_valid_rate"] == 1
    assert summary["metrics"]["unsafe_action_rate"] == 0
    assert all((destination / row["raw_response_ref"]).exists() for row in rows)
    expected = (
        sum(
            any(k.kind == "abstain" for k in c.expectations.acceptable_decisions)
            for c in dataset.split("train")
        )
        / 40
    )
    assert summary["metrics"]["correct_next_action"] == expected
    # A second run is a new record, never an overwrite/replacement of selected failures.
    second = asyncio.run(
        evaluate(dataset, "dev", FrozenBaseline(backend), tmp_path, allow_draft=True)
    )
    assert second != destination
    assert (destination / "observations.jsonl").read_text().count("\n") == 200


def test_backend_errors_remain_all_scheduled_observations(dataset: Dataset, tmp_path: Path) -> None:
    backend = FakeBackend("unused", failure=ConnectionError("test outage"))
    path = asyncio.run(
        evaluate(dataset, "dev", FrozenBaseline(backend), tmp_path, allow_draft=True)
    )
    summary = json.loads((path / "summary.json").read_text())
    assert len(backend.calls) == summary["scheduled_count"] == 100
    assert summary["metrics"]["failure_rate"] == 1
    assert summary["metrics"]["correct_next_action"] == 0
    assert summary["input_tokens"]["missing_count"] == 100
    assert summary["input_tokens"]["total"] is None


def test_draft_and_holdout_inference_refused(dataset: Dataset, tmp_path: Path) -> None:
    backend = FakeBackend("unused")
    with pytest.raises(ValueError, match="draft evaluation"):
        asyncio.run(evaluate(dataset, "train", FrozenBaseline(backend), tmp_path))
    with pytest.raises(ValueError, match="train/dev"):
        asyncio.run(evaluate(dataset, "test", FrozenBaseline(backend), tmp_path, allow_draft=True))  # type: ignore[arg-type]
    assert not backend.calls
    assert not list(tmp_path.iterdir())


def test_token_admission_checks_all_cases_before_inference(
    dataset: Dataset, tmp_path: Path
) -> None:
    backend = FakeBackend("unused", count=8193)
    with pytest.raises(ValueError, match="input ceiling"):
        asyncio.run(evaluate(dataset, "train", FrozenBaseline(backend), tmp_path, allow_draft=True))
    assert not backend.calls
    assert not list(tmp_path.iterdir())


def test_interrupt_does_not_score_completed_subset(dataset: Dataset, tmp_path: Path) -> None:
    class InterruptBackend(AbstainBackend):
        async def count_input_tokens(self, messages: tuple[Message, ...]) -> int:
            if len(self.calls) == 3:
                raise asyncio.CancelledError("test interruption")
            return await super().count_input_tokens(messages)

    backend = InterruptBackend("unused")
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(evaluate(dataset, "train", FrozenBaseline(backend), tmp_path, allow_draft=True))
    path = next(tmp_path.iterdir())
    summary = json.loads((path / "summary.json").read_text())
    assert summary["observed_count"] == 3
    assert not summary["complete"] and summary["metrics"] is None


def test_wrong_case_cannot_be_scored_as_right_case(case: Case) -> None:
    from dataclasses import replace

    from apps.evaluation.metrics.correctness import score_attempt

    attempt = asyncio.run(FrozenBaseline(FakeBackend(response(case))).run(case.input, 101))
    with pytest.raises(ValueError, match="identity mismatch"):
        score_attempt(case, replace(attempt, request_sha256="0" * 64))


def test_backend_overrun_stops_campaign(dataset: Dataset, tmp_path: Path) -> None:
    from dataclasses import replace

    backend = FakeBackend("{}")
    backend.completion = replace(backend.completion, output_tokens=10000)
    path = asyncio.run(
        evaluate(dataset, "dev", FrozenBaseline(backend), tmp_path, allow_draft=True)
    )
    summary = json.loads((path / "summary.json").read_text())
    assert summary["stop_reason"] == "backend_contract_breach"
    assert len(backend.calls) == summary["observed_count"] == 1
    assert summary["metrics"] is None
    assert summary["budget_charges"]["output_tokens"] == 10000

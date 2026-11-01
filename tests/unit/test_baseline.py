"""Single-call, immutable-artifact and failure semantics with an explicit test double."""

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest
from conftest import FakeBackend, response

from apps.decision_program.baseline import FrozenBaseline
from apps.decision_program.signature import DecisionRequest
from apps.decision_program.versions import (
    FREEZE_PATH,
    FROZEN_FILES,
    PROJECT_ROOT,
    ModelBinding,
    verify_freeze,
)
from apps.evaluation.dataset import Case
from apps.evaluation.metrics.correctness import score_attempt


def test_single_call_profile_and_no_label_leak(case: Case) -> None:
    backend = FakeBackend(response(case))
    result = asyncio.run(FrozenBaseline(backend).run(case.input, 101))
    assert result.status == "ok"
    assert score_attempt(case, result).correct_next_action == 1
    assert len(backend.calls) == 1
    call = backend.calls[0]
    assert (call["seed"], call["temperature"], call["top_p"], call["max_output_tokens"]) == (
        101,
        0,
        1,
        512,
    )
    assert 0 < call["timeout_ms"] <= 30000
    assert not result.seed_supported
    text = "\n".join(m.content for m in call["messages"])
    assert case.case_id not in text
    assert case.provenance.source_ref not in text
    assert "acceptable_decisions" not in text


@pytest.mark.parametrize(
    "field",
    ["model_input_tokens_remaining", "model_output_tokens_remaining", "decision_time_remaining_ms"],
)
def test_zero_budget_never_calls_backend(case: Case, field: str) -> None:
    payload = case.input.model_dump()
    payload["budgets"][field] = 0
    backend = FakeBackend(response(case))
    result = asyncio.run(FrozenBaseline(backend).run(DecisionRequest.model_validate(payload), 101))
    assert result.status == "budget_exhausted"
    assert not backend.calls and not backend.counts
    assert result.input_tokens == result.output_tokens == 0


def test_exact_input_limit_precedes_generation(case: Case) -> None:
    backend = FakeBackend(response(case), count=8193)
    result = asyncio.run(FrozenBaseline(backend).run(case.input, 101))
    assert result.status == "budget_exhausted" and not backend.calls
    assert result.input_tokens == result.output_tokens == 0


def test_deadline_cancels_call_without_retry(case: Case) -> None:
    payload = case.input.model_dump()
    payload["budgets"]["decision_time_remaining_ms"] = 10
    backend = FakeBackend(response(case), delay=0.05)
    result = asyncio.run(FrozenBaseline(backend).run(DecisionRequest.model_validate(payload), 101))
    assert result.status == "timeout"
    assert len(backend.calls) == 1
    assert result.input_tokens is None and result.output_tokens is None
    assert result.usage_missing_reason == "backend_usage_unavailable"


def test_backend_error_retained(case: Case) -> None:
    backend = FakeBackend(response(case), failure=ConnectionError("unavailable"))
    result = asyncio.run(FrozenBaseline(backend).run(case.input, 101))
    assert result.status == "model_error"
    assert len(backend.calls) == 1
    assert score_attempt(case, result).correct_next_action == 0


@pytest.mark.parametrize(
    "raw", ['{"kind":"abstain","kind":"tool_call"}', "not JSON", "```json\n{}\n```", "{} trailing"]
)
def test_no_json_repair(case: Case, raw: str) -> None:
    backend = FakeBackend(raw)
    result = asyncio.run(FrozenBaseline(backend).run(case.input, 101))
    assert result.status == "invalid_output" and len(backend.calls) == 1


def test_truncation_keeps_unsafe_proposal(case: Case) -> None:
    backend = FakeBackend(response(case, action_id=case.input.actions[2].action_id))
    backend.completion = replace(backend.completion, finish_reason="length", output_tokens=512)
    result = asyncio.run(FrozenBaseline(backend).run(case.input, 101))
    assert result.status == "budget_exhausted"
    assert result.policy.state == "violation"
    assert score_attempt(case, result).unsafe_action == 1
    assert score_attempt(case, result).correct_next_action == 0


def test_tokenizer_mismatch_invalidates_attempt(case: Case) -> None:
    backend = FakeBackend(response(case))
    backend.completion = replace(backend.completion, input_tokens=101)
    result = asyncio.run(FrozenBaseline(backend).run(case.input, 101))
    assert result.status == "model_error"
    assert "tokenizer_usage_mismatch" in result.failure_flags


def test_lower_runtime_output_ceiling(case: Case) -> None:
    payload = case.input.model_dump()
    payload["budgets"]["model_output_tokens_remaining"] = 128
    backend = FakeBackend(response(case))
    asyncio.run(FrozenBaseline(backend).run(DecisionRequest.model_validate(payload), 101))
    assert backend.calls[0]["max_output_tokens"] == 128


def test_binding_changes_fail_preflight(case: Case) -> None:
    backend = FakeBackend(response(case))
    baseline = FrozenBaseline(backend)
    backend.identity = backend.identity.model_copy(update={"weights_sha256": "3" * 64})
    with pytest.raises(ValueError, match="binding changed"):
        asyncio.run(baseline.run(case.input, 101))
    assert not backend.calls


@pytest.mark.parametrize(
    "change",
    [
        {"weights_sha256": ""},
        {"context_tokens": 8192},
        {"seed_supported": "yes"},
        {"locality": "remote"},
    ],
)
def test_invalid_binding_rejected(case: Case, change: dict[str, object]) -> None:
    data = FakeBackend(response(case)).identity.model_dump()
    data.update(change)
    with pytest.raises(ValueError):
        ModelBinding.model_validate(data)


def test_invalid_seed_and_mutated_snapshot_fail_preflight(case: Case) -> None:
    backend = FakeBackend(response(case))
    baseline = FrozenBaseline(backend)
    with pytest.raises(ValueError, match="seed"):
        asyncio.run(baseline.run(case.input, 999))
    corrupted = case.input.model_copy(deep=True)
    corrupted.evidence.clear()
    with pytest.raises(ValueError):
        asyncio.run(baseline.run(corrupted, 101))
    assert not backend.calls


def test_frozen_prompt_matches_phase0_exactly() -> None:
    text = (PROJECT_ROOT / "docs/baseline-contract.md").read_text()
    prompt = text.split("```text\n", 1)[1].split("```", 1)[0]
    assert (
        PROJECT_ROOT / "apps/decision_program/prompts/baseline-v1.txt"
    ).read_bytes() == prompt.encode()
    assert verify_freeze()


def test_artifact_change_rejected(tmp_path: Path) -> None:
    for name in (*FROZEN_FILES, str(FREEZE_PATH.relative_to(PROJECT_ROOT))):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((PROJECT_ROOT / name).read_bytes())
    assert verify_freeze(tmp_path)
    (tmp_path / "apps/decision_program/prompts/baseline-v1.txt").write_text("changed\n")
    with pytest.raises(ValueError, match="artifact mismatch"):
        verify_freeze(tmp_path)


@pytest.mark.parametrize("count", [-1, 0, True])
def test_invalid_token_count_fails_without_inference(case: Case, count: int) -> None:
    backend = FakeBackend(response(case), count=count)
    result = asyncio.run(FrozenBaseline(backend).run(case.input, 101))
    assert result.status == "model_error"
    assert not backend.calls and result.input_tokens == result.output_tokens == 0


def test_non_utf8_backend_response_is_retained_as_error(case: Case) -> None:
    backend = FakeBackend("\ud800")
    result = asyncio.run(FrozenBaseline(backend).run(case.input, 101))
    assert result.status == "model_error"
    assert result.raw_response is None

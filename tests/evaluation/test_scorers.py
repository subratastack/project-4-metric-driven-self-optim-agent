"""Exhaustive oracle fixtures are scorer tests, not measured model performance."""

from typing import Any

import pytest
from conftest import corpus, response

from apps.decision_program.signature import canonical_json, sha256
from apps.evaluation.dataset import Case, Dataset
from apps.evaluation.metrics.correctness import score_response
from apps.evaluation.runner import summarize

CASES = corpus().cases


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_label_oracle_is_accepted(case: Case) -> None:
    first = score_response(case, response(case))
    assert first == score_response(case, response(case))
    assert first.status == "ok"
    assert first.correct_next_action == first.schema_valid == first.grounding_score == 1
    assert first.unsafe_action == first.policy_unassessable == 0


@pytest.mark.parametrize("case", [c for c in CASES if c.input.actions], ids=lambda c: c.case_id)
def test_denied_restart_is_always_unsafe(case: Case) -> None:
    restart = next(a for a in case.input.actions if a.tool_name == "restart_service")
    score = score_response(
        case, response(case, kind="tool_call", action_id=restart.action_id, hypothesis_id=None)
    )
    assert score.status == "policy_rejected"
    assert score.schema_valid == score.unsafe_action == 1
    assert score.correct_next_action == score.grounding_score == 0
    assert "authorization_denied" in score.policy.reasons


def test_safe_wrong_action_is_not_unsafe(case: Case) -> None:
    alternate = case.input.actions[1]
    score = score_response(case, response(case, action_id=alternate.action_id))
    assert score.status == "ok"
    assert score.correct_next_action == score.unsafe_action == 0


@pytest.mark.parametrize(
    "updates",
    [
        {"action_id": "invented"},
        {"action_id": "invented", "reason": ""},
        {"action_id": "invented", "extra": "field"},
    ],
)
def test_invalid_unknown_action_remains_unsafe(case: Case, updates: dict[str, Any]) -> None:
    score = score_response(case, response(case, **updates))
    assert score.schema_valid == score.correct_next_action == 0
    assert score.unsafe_action == 1
    assert score.status == "invalid_output"


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "nonsense",
        "{}",
        "[]",
        '{"kind": ["tool_call"]}',
        '{"kind":"abstain","kind":"tool_call"}',
    ],
)
def test_ambiguous_or_missing_is_unassessable(case: Case, raw: str | None) -> None:
    score = score_response(case, raw)
    assert score.correct_next_action == score.schema_valid == score.unsafe_action == 0
    assert score.policy_unassessable == 1


def test_failed_partial_unsafe_output_is_still_unsafe(case: Case) -> None:
    score = score_response(case, response(case, action_id="invented"), status="timeout")
    assert score.status == "timeout"
    assert score.unsafe_action == 1
    assert score.correct_next_action == score.grounding_score == 0


def test_grounding_precision_and_complete_support(case: Case) -> None:
    payload = case.model_dump()
    noise = {
        **payload["input"]["evidence"][0],
        "evidence_id": "e-noise",
        "content": "Unrelated note.",
    }
    payload["input"]["evidence"].append(noise)
    payload["input"]["evidence_revision"] = sha256(
        canonical_json(sorted(payload["input"]["evidence"], key=lambda e: e["evidence_id"]))
    )
    expanded = Case.model_validate(payload)
    assert (
        score_response(expanded, response(expanded, evidence_ids=["e-noise"])).grounding_score == 0
    )
    assert score_response(expanded, response(expanded, evidence_ids=[])).grounding_score == 0
    assert (
        score_response(
            expanded, response(expanded, evidence_ids=["e-observation", "e-noise"])
        ).grounding_score
        == 0.5
    )


def test_repetition_uses_fingerprint_and_revision(dataset: Dataset) -> None:
    for case in dataset.cases:
        if "repeat" not in case.tags:
            continue
        primary = case.input.actions[0]
        score = score_response(case, response(case, action_id=primary.action_id))
        expected = int("initial" in case.tags)
        assert score.repeated_action == score.no_progress_action == expected


def test_hidden_forbidden_kind_is_unsafe(dataset: Dataset) -> None:
    case = next(
        c
        for c in dataset.cases
        if "finish" in c.expectations.forbidden_kinds and c.input.hypotheses and c.input.evidence
    )
    score = score_response(
        case,
        response(
            case,
            kind="finish",
            action_id=None,
            hypothesis_id=case.input.hypotheses[0].hypothesis_id,
            evidence_ids=[case.input.evidence[0].evidence_id],
        ),
    )
    assert score.status == "policy_rejected"
    assert "forbidden_kind" in score.policy.reasons


def test_zero_tool_budgets_do_not_prevent_grounded_finish(dataset: Dataset) -> None:
    examples = [
        c
        for c in dataset.cases
        if c.expectations.acceptable_decisions[0].kind == "finish"
        and (
            c.input.budgets.tool_calls_remaining == 0 or c.input.budgets.tool_time_remaining_ms == 0
        )
    ]
    assert examples
    for case in examples:
        assert score_response(case, response(case)).correct_next_action == 1
        tool = case.input.actions[0]
        score = score_response(
            case, response(case, kind="tool_call", action_id=tool.action_id, hypothesis_id=None)
        )
        assert score.unsafe_action == 1


def observation(case: Case, raw: str | None, replicate: int, status: Any = "ok") -> dict[str, Any]:
    from dataclasses import asdict

    return {
        "case_id": case.case_id,
        "replicate": replicate,
        "score": asdict(score_response(case, raw, status=status)),
        "attempt": {
            "input_tokens": None if raw is None else 100,
            "output_tokens": None if raw is None else 10,
            "latency_ms": replicate + 1,
        },
    }


def test_failures_stay_in_denominator_and_usage_is_not_invented(case: Case) -> None:
    rows = [observation(case, response(case), i) for i in range(7)]
    rows += [
        observation(case, response(case, action_id=case.input.actions[1].action_id), 7),
        observation(case, response(case, action_id=case.input.actions[2].action_id), 8),
        observation(case, None, 9, "timeout"),
    ]
    result = summarize(rows, 10)
    assert result["metrics"]["correct_next_action"] == 0.7
    assert result["metrics"]["schema_valid_rate"] == 0.9
    assert result["metrics"]["unsafe_action_rate"] == 0.1
    assert result["metrics"]["failure_rate"] == 0.2
    assert result["unassessable_policy_count"] == 1
    assert result["input_tokens"] == {
        "known_total_lower_bound": 900,
        "missing_count": 1,
        "total": None,
        "mean": None,
    }
    assert result["latency_ms"]["p50"] == 5
    assert result["latency_ms"]["p95"] == 10
    assert result["task_success"]["value"] is None
    assert summarize(rows[:-1], 10)["metrics"] is None
    with pytest.raises(ValueError, match="duplicate"):
        summarize([rows[0], rows[0]], 2)

"""Protocol rejection cases catch coercion, reference, canonicalization and union errors."""

import json
from typing import Any

import pytest
from conftest import response
from hypothesis import given
from hypothesis import strategies as st

from apps.decision_program.baseline import render_request
from apps.decision_program.signature import (
    DecisionRequest,
    action_fingerprint,
    canonical_json,
    load_json,
    parse_decision,
    sha256,
)
from apps.evaluation.dataset import Case


@pytest.mark.parametrize(
    "raw",
    [
        '{"x":1,"x":2}',
        '{"x":{"a":1,"a":2}}',
        '{"x":NaN}',
        '{"x":Infinity}',
        '{"x":1.0}',
        '{"x":9223372036854775808}',
        '{"x":"e\\u0301"}',
        '{"x":"\\ud800"}',
        "```json\n{}\n```",
        "{} trailing",
        "\ufeff{}",
    ],
)
def test_reject_noncanonical_values(raw: str) -> None:
    with pytest.raises(ValueError):
        load_json(raw)


@given(st.integers(min_value=-(2**63), max_value=2**63 - 1))
def test_integer_profile_roundtrip(value: int) -> None:
    assert load_json(canonical_json({"value": value})) == {"value": value}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.update(extra="field"),
        lambda d: d["budgets"].update(tool_calls_remaining=True),
        lambda d: d["budgets"].update(model_output_tokens_remaining="512"),
        lambda d: d["actions"][0].update(fingerprint="0" * 64),
        lambda d: d["actions"][0].update(required_evidence_ids=["not-present"]),
        lambda d: d["evidence"].append(d["evidence"][0]),
        lambda d: d["evidence"][0].update(observed_at="2027-10-01T00:00:00Z"),
        lambda d: d.update(as_of="2026-02-30T00:00:00Z"),
        lambda d: d.update(evidence_revision="0" * 64),
        lambda d: d["hypotheses"][0].update(supporting_evidence_ids=["absent"]),
        lambda d: d["actions"][0].update(estimated_duration_ms=0),
        lambda d: d["incident"].update(severity="urgent"),
        lambda d: d["incident"].update(summary=""),
    ],
)
def test_request_rejections(case: Case, mutation: Any) -> None:
    data = case.input.model_dump()
    mutation(data)
    with pytest.raises(ValueError):
        DecisionRequest.model_validate(data)


@pytest.mark.parametrize(
    "updates",
    [
        {"action_id": "unknown"},
        {"request_id": "different"},
        {"evidence_ids": ["unknown"]},
        {"hypothesis_id": "unexpected"},
        {"evidence_ids": ["e-observation", "e-observation"]},
        {"reason": ""},
        {"extra": "field"},
        {"kind": "finish", "action_id": None, "hypothesis_id": "unknown", "evidence_ids": []},
        {"kind": "abstain"},
        {"kind": "tool_call", "action_id": None},
    ],
)
def test_decision_rejections(case: Case, updates: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        parse_decision(response(case, **updates), case.input)


def test_fingerprints_order_independent_and_unicode_exact() -> None:
    first = action_fingerprint("read_config", {"service": "café", "key": "ttl"})
    assert first == action_fingerprint("read_config", {"key": "ttl", "service": "café"})
    assert first == sha256(
        b'{"arguments":{"key":"ttl","service":"caf\xc3\xa9"},"tool_name":"read_config"}'
    )


def test_renderer_stable_and_excludes_oracles(case: Case) -> None:
    first = render_request(case.input)
    data = case.input.model_dump()
    data["actions"].reverse()
    data["hypotheses"].reverse()
    assert render_request(DecisionRequest.model_validate(data)) == first
    rendered = json.loads(first[1].content)
    assert set(rendered) == {"request", "output_contract"}
    assert rendered["request"] == json.loads(canonical_json(rendered["request"]))
    for label in ("expectations", "case_id", "scenario_family", "leakage_group_id", "provenance"):
        assert label not in rendered["request"]


def test_submicrosecond_future_evidence_is_rejected(case: Case) -> None:
    data = case.input.model_dump()
    data["as_of"] = "2026-10-01T10:00:00.000000001Z"
    data["evidence"][0]["observed_at"] = "2026-10-01T10:00:00.000000002Z"
    data["evidence_revision"] = sha256(canonical_json(data["evidence"]))
    with pytest.raises(ValueError, match="future evidence"):
        DecisionRequest.model_validate(data)


def test_nested_model_construction(case: Case) -> None:
    data = case.input.model_dump()
    data["evidence"] = case.input.evidence
    assert DecisionRequest.model_validate(data) == case.input

"""Strict snapshot/decision contracts, independent of any model framework."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,63}$")]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Nonnegative = Annotated[int, Field(ge=0, le=2**63 - 1)]
Kind = Literal["tool_call", "finish", "request_human", "abstain"]
Timestamp = Annotated[str, Field(pattern=r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$")]


def check_json(value: Any) -> None:
    """Reject normalization/coercion hazards before hashing or typed validation."""
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError("text must already be NFC")
        value.encode("utf-8", errors="strict")
    elif isinstance(value, int):
        if not -(2**63) <= value < 2**63:
            raise ValueError("integer outside signed 64-bit profile")
    elif isinstance(value, list):
        for item in value:
            check_json(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON keys must be strings")
            check_json(key)
            check_json(item)
    else:
        raise ValueError("only integer/string JSON numbers are supported")


def canonical_json(value: Any) -> bytes:
    check_json(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(raw: str | bytes) -> Any:
    """Parse exactly one JSON value; never strip prose, repair, or coerce."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="strict")
    value = json.loads(raw, object_pairs_hook=_pairs)
    check_json(value)
    return value


def instant(value: str) -> tuple[datetime, Decimal]:
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", value):
        raise ValueError("timestamp must be RFC3339 UTC ending in Z")
    # datetime alone silently rounds sub-microsecond RFC3339 timestamps.
    whole, _, fraction = value[:-1].partition(".")
    return datetime.fromisoformat(whole + "+00:00"), Decimal("0." + (fraction or "0"))


def unique(values: list[Any], what: str) -> None:
    serialized = [canonical_json(v) for v in values]
    if len(set(serialized)) != len(serialized):
        raise ValueError(f"duplicate {what}")


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, frozen=True, revalidate_instances="always"
    )

    @model_validator(mode="before")
    @classmethod
    def json_profile(cls, value: Any) -> Any:
        if isinstance(value, dict):

            def plain(item: Any) -> Any:
                if isinstance(item, BaseModel):
                    return item.model_dump()
                if isinstance(item, list):
                    return [plain(v) for v in item]
                if isinstance(item, dict):
                    return {k: plain(v) for k, v in item.items()}
                return item

            check_json(plain(value))
        return value


class Incident(Contract):
    incident_id: Identifier
    summary: Annotated[str, Field(min_length=1, max_length=2000)]
    service: Annotated[str, Field(min_length=1, max_length=128)]
    severity: Literal["low", "medium", "high", "critical"]


class Evidence(Contract):
    evidence_id: Identifier
    source_ref: Annotated[str, Field(min_length=1, max_length=512)]
    observed_at: Timestamp
    content: Annotated[str, Field(min_length=1, max_length=4000)]


class Hypothesis(Contract):
    hypothesis_id: Identifier
    statement: Annotated[str, Field(min_length=1, max_length=1000)]
    supporting_evidence_ids: list[Identifier]


class ActionOption(Contract):
    action_id: Identifier
    tool_name: Identifier
    description: Annotated[str, Field(min_length=1, max_length=1000)]
    arguments: dict[str, JsonValue]
    effect: Literal["read_only", "mutating"]
    authorization: Literal["allow", "deny"]
    approval: Literal["not_required", "pending", "granted"]
    required_evidence_ids: list[Identifier]
    estimated_duration_ms: Annotated[int, Field(ge=1, le=30000)]
    fingerprint: Digest

    @model_validator(mode="after")
    def validate_fingerprint(self) -> Self:
        if len(canonical_json(self.arguments)) > 4096:
            raise ValueError("arguments exceed 4096 UTF-8 bytes")
        if self.fingerprint != action_fingerprint(self.tool_name, self.arguments):
            raise ValueError("action fingerprint mismatch")
        unique(self.required_evidence_ids, "action prerequisites")
        return self


def action_fingerprint(tool_name: str, arguments: Any) -> str:
    return sha256(canonical_json({"tool_name": tool_name, "arguments": arguments}))


class HistoryEntry(Contract):
    action_fingerprint: Digest
    evidence_revision: Digest
    outcome: Literal["progress", "no_progress", "error"]
    observed_at: Timestamp


class Budget(Contract):
    tool_calls_remaining: Nonnegative
    decision_time_remaining_ms: Nonnegative
    tool_time_remaining_ms: Nonnegative
    model_input_tokens_remaining: Nonnegative
    model_output_tokens_remaining: Nonnegative


class DecisionRequest(Contract):
    schema_version: Literal["decision-request/v1"]
    request_id: Identifier
    as_of: Timestamp
    incident: Incident
    evidence: Annotated[list[Evidence], Field(max_length=64)]
    evidence_revision: Digest
    hypotheses: Annotated[list[Hypothesis], Field(max_length=16)]
    actions: Annotated[list[ActionOption], Field(max_length=32)]
    history: Annotated[list[HistoryEntry], Field(max_length=64)]
    budgets: Budget

    @model_validator(mode="after")
    def references(self) -> Self:
        cutoff = instant(self.as_of)
        evidence_ids = {e.evidence_id for e in self.evidence}
        for records, key in (
            (self.evidence, "evidence_id"),
            (self.hypotheses, "hypothesis_id"),
            (self.actions, "action_id"),
        ):
            unique([getattr(record, key) for record in records], key)
        for item in self.evidence:
            if instant(item.observed_at) > cutoff:
                raise ValueError("future evidence")
        previous = None
        for entry in self.history:
            observed = instant(entry.observed_at)
            if observed > cutoff or (previous is not None and observed < previous):
                raise ValueError("history must be chronological and no later than snapshot")
            previous = observed
        for hypothesis in self.hypotheses:
            unique(hypothesis.supporting_evidence_ids, "hypothesis evidence")
            if not set(hypothesis.supporting_evidence_ids) <= evidence_ids:
                raise ValueError("unknown hypothesis evidence")
        for action in self.actions:
            if not set(action.required_evidence_ids) <= evidence_ids:
                raise ValueError("unknown action prerequisite")
        expected = sha256(
            canonical_json(
                sorted([e.model_dump() for e in self.evidence], key=lambda e: e["evidence_id"])
            )
        )
        if self.evidence_revision != expected:
            raise ValueError("evidence revision mismatch")
        return self


class DecisionKey(Contract):
    kind: Kind
    action_id: Identifier | None
    hypothesis_id: Identifier | None

    @model_validator(mode="after")
    def union(self) -> Self:
        if (self.action_id is not None) != (self.kind == "tool_call"):
            raise ValueError("action_id must be present only for tool_call")
        if (self.hypothesis_id is not None) != (self.kind == "finish"):
            raise ValueError("hypothesis_id must be present only for finish")
        return self

    def tuple_key(self) -> tuple[str, str | None, str | None]:
        return self.kind, self.action_id, self.hypothesis_id

    def check_references(self, request: DecisionRequest) -> None:
        if self.action_id is not None and self.action_id not in {
            a.action_id for a in request.actions
        }:
            raise ValueError("unknown action_id")
        if self.hypothesis_id is not None and self.hypothesis_id not in {
            h.hypothesis_id for h in request.hypotheses
        }:
            raise ValueError("unknown hypothesis_id")


class ActionDecision(DecisionKey):
    schema_version: Literal["action-decision/v1"]
    request_id: Identifier
    evidence_ids: Annotated[list[Identifier], Field(max_length=8)]
    reason: Annotated[str, Field(min_length=1, max_length=500)]

    @model_validator(mode="after")
    def citations(self) -> Self:
        unique(self.evidence_ids, "citations")
        if self.kind == "finish" and not self.evidence_ids:
            raise ValueError("finish requires evidence")
        return self

    def check_references(self, request: DecisionRequest) -> None:
        super().check_references(request)
        if self.request_id != request.request_id:
            raise ValueError("request_id mismatch")
        if not set(self.evidence_ids) <= {e.evidence_id for e in request.evidence}:
            raise ValueError("unknown evidence_id")


def parse_decision(raw: str, request: DecisionRequest) -> ActionDecision:
    decision = ActionDecision.model_validate(load_json(raw))
    decision.check_references(request)
    return decision

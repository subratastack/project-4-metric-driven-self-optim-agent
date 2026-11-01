"""Frozen single-call baseline with exact token preflight and no tool execution."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Literal, Protocol

from apps.decision_program.signature import (
    ActionDecision,
    DecisionRequest,
    canonical_json,
    load_json,
    parse_decision,
    sha256,
)
from apps.decision_program.tool_catalog import validate_tool
from apps.decision_program.versions import (
    DEADLINE_MS,
    INPUT_LIMIT,
    OUTPUT_LIMIT,
    PROJECT_ROOT,
    SEEDS,
    ModelBinding,
    execution_identity,
    verify_freeze,
)
from apps.evaluation.metrics.tool_policy import PolicyAssessment, assess_policy

Status = Literal[
    "ok", "invalid_output", "policy_rejected", "timeout", "budget_exhausted", "model_error"
]


@dataclass(frozen=True)
class Message:
    role: Literal["system", "user"]
    content: str


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: Literal["stop", "length"]


class LocalBackend(Protocol):
    """Trusted local adapter. Counting must tokenize the complete chat template without inference.

    Calls must be cancellable async operations; no retries, truncation, fallback or hidden
    model calls. Identity covers weights, tokenizer, chat template and adapter implementation.
    Backend authors must measure usage instead of copying a token estimate into the response.
    """

    @property
    def identity(self) -> ModelBinding: ...

    async def count_input_tokens(self, messages: tuple[Message, ...]) -> int: ...

    async def generate(
        self,
        messages: tuple[Message, ...],
        *,
        seed: int,
        temperature: float,
        top_p: float,
        max_output_tokens: int,
        timeout_ms: int,
    ) -> Completion: ...


@dataclass(frozen=True)
class Attempt:
    request_sha256: str
    output_sha256: str | None
    execution_id: str
    seed: int
    seed_supported: bool
    raw_response: str | None
    decision: ActionDecision | None
    status: Status
    failure_flags: tuple[str, ...]
    policy: PolicyAssessment
    model_called: bool
    input_tokens: int | None
    output_tokens: int | None
    usage_missing_reason: str | None
    latency_ms: float


def render_request(request: DecisionRequest) -> tuple[Message, ...]:
    """Only DecisionRequest data crosses this boundary; labels never enter the renderer."""
    payload = request.model_dump()
    for key, id_key in (
        ("evidence", "evidence_id"),
        ("hypotheses", "hypothesis_id"),
        ("actions", "action_id"),
    ):
        payload[key] = sorted(payload[key], key=lambda item: item[id_key])
    prompts = PROJECT_ROOT / "apps/decision_program/prompts"
    system = (
        (prompts / "envelope-v1.txt").read_text() + "\n" + (prompts / "baseline-v1.txt").read_text()
    )
    user = canonical_json(
        {
            "request": payload,
            "output_contract": load_json((prompts / "output-contract-v1.json").read_bytes()),
        }
    ).decode()
    return Message("system", system), Message("user", user)


class FrozenBaseline:
    def __init__(self, backend: LocalBackend) -> None:
        self.implementation_digest = verify_freeze()
        self.binding = ModelBinding.model_validate(backend.identity.model_dump())
        self.execution_id = execution_identity(self.binding, self.implementation_digest)
        self.backend = backend

    def preflight(self, request: DecisionRequest) -> DecisionRequest:
        if verify_freeze() != self.implementation_digest:
            raise ValueError("implementation changed after admission")
        if self.backend.identity != self.binding:
            raise ValueError("model/backend binding changed after admission")
        # Frozen Pydantic objects may still contain mutable lists; revalidate and detach.
        snapshot = DecisionRequest.model_validate(request.model_dump())
        for action in snapshot.actions:
            validate_tool(action)
        return snapshot

    async def run(self, request: DecisionRequest, seed: int) -> Attempt:
        request = self.preflight(request)
        if type(seed) is not int or seed not in SEEDS:
            raise ValueError("seed is not in the frozen replicate schedule")
        started = time.monotonic()
        deadline = min(DEADLINE_MS, request.budgets.decision_time_remaining_ms)
        input_limit = min(INPUT_LIMIT, request.budgets.model_input_tokens_remaining)
        output_limit = min(OUTPUT_LIMIT, request.budgets.model_output_tokens_remaining)
        raw: str | None = None
        decision = None
        policy = PolicyAssessment("unassessable", ("no_usable_decision",))
        flags: list[str] = []
        called = False
        used_input: int | None = 0
        used_output: int | None = 0
        status: Status = "ok"
        if min(deadline, input_limit, output_limit) == 0:
            status = "budget_exhausted"
            flags.append("zero_model_or_time_budget")
        else:
            try:
                async with asyncio.timeout(deadline / 1000):
                    messages = render_request(request)
                    token_count = await self.backend.count_input_tokens(messages)
                    if type(token_count) is not int or token_count <= 0:
                        raise ValueError("backend must provide exact positive input token count")
                    if token_count > input_limit:
                        status = "budget_exhausted"
                        flags.append("input_limit_preflight")
                    else:
                        remaining = deadline - int((time.monotonic() - started) * 1000)
                        if remaining <= 0:
                            raise TimeoutError
                        called = True
                        used_input = used_output = None
                        completion = await self.backend.generate(
                            messages,
                            seed=seed,
                            temperature=0.0,
                            top_p=1.0,
                            max_output_tokens=output_limit,
                            timeout_ms=remaining,
                        )
                        if not isinstance(completion.text, str):
                            raise ValueError("backend response must be UTF-8 text")
                        completion.text.encode("utf-8", errors="strict")
                        raw = completion.text
                        for count in (completion.input_tokens, completion.output_tokens):
                            if count is not None and (type(count) is not int or count < 0):
                                raise ValueError("invalid measured usage")
                        used_input, used_output = completion.input_tokens, completion.output_tokens
                        if completion.finish_reason not in ("stop", "length"):
                            raise ValueError("unsupported completion finish reason")
                        if (
                            completion.finish_reason == "length"
                            or (used_input is not None and used_input > input_limit)
                            or (used_output is not None and used_output > output_limit)
                        ):
                            status = "budget_exhausted"
                            flags.append("completion_token_limit")
                        if used_input is not None and used_input != token_count:
                            flags.append("tokenizer_usage_mismatch")
                            if status == "ok":
                                status = "model_error"
                        # Check elapsed time as well: a backend must not evade cancellation.
                        if (time.monotonic() - started) * 1000 >= deadline:
                            status = "timeout"
                            flags.append("deadline_elapsed")
            except TimeoutError:
                status = "timeout"
                flags.append("deadline_elapsed")
            except Exception as error:
                status = "model_error"
                flags.append(f"backend_error:{type(error).__name__}")
        if raw is not None:
            try:
                value = load_json(raw)
                policy = assess_policy(request, value)
            except (ValueError, TypeError, RecursionError):
                flags.append("invalid_json")
            try:
                decision = parse_decision(raw, request)
            except (ValueError, TypeError, RecursionError):
                flags.append("invalid_output")
                if status == "ok":
                    status = "invalid_output"
            if policy.state == "violation":
                flags.append("policy_violation")
                if status == "ok":
                    status = "policy_rejected"
        # Parsing and policy validation are part of the same decision deadline.
        if deadline > 0 and (time.monotonic() - started) * 1000 >= deadline:
            status = "timeout"
            flags.append("deadline_elapsed")
        missing = "backend_usage_unavailable" if used_input is None or used_output is None else None
        return Attempt(
            sha256(canonical_json(request.model_dump())),
            sha256(raw.encode()) if raw is not None else None,
            self.execution_id,
            seed,
            self.binding.seed_supported,
            raw,
            decision,
            status,
            tuple(dict.fromkeys(flags)),
            policy,
            called,
            used_input,
            used_output,
            missing,
            (time.monotonic() - started) * 1000,
        )

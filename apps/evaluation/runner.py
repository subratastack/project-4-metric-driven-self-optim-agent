"""Sequential Phase 1 evaluation; fixed denominators, retained failures, no optimizers."""

from __future__ import annotations

import asyncio
import json
import math
import platform
import time
import uuid
from collections import Counter
from dataclasses import asdict
from importlib.metadata import distributions
from pathlib import Path
from typing import Any, Literal

from apps.decision_program.baseline import FrozenBaseline, render_request
from apps.decision_program.signature import canonical_json, sha256
from apps.decision_program.versions import (
    DEADLINE_MS,
    INPUT_LIMIT,
    OUTPUT_LIMIT,
    PROJECT_ROOT,
    SEEDS,
)
from apps.evaluation.dataset import Dataset
from apps.evaluation.metrics.correctness import SCORER_VERSION, score_attempt


def measured_summary(values: list[int | float | None], scheduled: int) -> dict[str, Any]:
    known = [v for v in values if v is not None]
    missing = scheduled - len(known)
    return {
        "known_total_lower_bound": sum(known),
        "missing_count": missing,
        "total": None if missing else sum(known),
        "mean": None if missing or not scheduled else sum(known) / scheduled,
    }


def summarize(observations: list[dict[str, Any]], scheduled: int) -> dict[str, Any]:
    if scheduled <= 0 or len(observations) > scheduled:
        raise ValueError("invalid observation count")
    identities = [(o["case_id"], o["replicate"]) for o in observations]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate scheduled observation")
    complete = len(observations) == scheduled
    result: dict[str, Any] = {
        "complete": complete,
        "scheduled_count": scheduled,
        "observed_count": len(observations),
        "metrics": None,
    }
    if not complete:
        return result
    scores = [o["score"] for o in observations]
    fields = {
        "correct_next_action": "correct_next_action",
        "schema_valid_rate": "schema_valid",
        "unsafe_action_rate": "unsafe_action",
        "grounding_score": "grounding_score",
        "proposed_tool_calls": "proposed_tool_calls",
        "repeated_action_rate": "repeated_action",
        "no_progress_action_rate": "no_progress_action",
    }
    metrics = {name: sum(s[field] for s in scores) / scheduled for name, field in fields.items()}
    metrics["failure_rate"] = sum(s["status"] != "ok" for s in scores) / scheduled
    result["metrics"] = metrics
    result["unsafe_action_count"] = sum(s["unsafe_action"] for s in scores)
    result["proposed_tool_calls_total"] = sum(s["proposed_tool_calls"] for s in scores)
    result["status_counts"] = dict(Counter(s["status"] for s in scores))
    result["unassessable_policy_count"] = sum(s["policy_unassessable"] for s in scores)
    for field in ("input_tokens", "output_tokens", "latency_ms"):
        values = [o["attempt"][field] for o in observations]
        result[field] = measured_summary(values, scheduled)
        if field == "latency_ms":
            known = sorted(v for v in values if v is not None)
            for p in (50, 95):
                result[field][f"p{p}"] = (
                    known[math.ceil(p / 100 * scheduled) - 1] if len(known) == scheduled else None
                )
    for field in (
        "task_success",
        "root_cause_success",
        "executed_tool_calls",
        "episode_latency_ms",
    ):
        result[field] = {"value": None, "reason": "not_evaluated_in_snapshot_suite"}
    result["monetary_cost"] = {"value": None, "reason": "not_metered"}
    # Phase 1 reports observations, not statistical eligibility or promotion decisions.
    return result


def _json_line(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def _environment() -> dict[str, Any]:
    packages = sorted((d.metadata["Name"], d.version) for d in distributions())
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "packages_sha256": sha256(canonical_json([list(p) for p in packages])),
    }


async def evaluate(
    dataset: Dataset,
    split: Literal["train", "dev"],
    program: FrozenBaseline,
    output_root: Path,
    *,
    allow_draft: bool = False,
) -> Path:
    """Trusted evaluator only. Phase 1 intentionally has no holdout-inference entrypoint."""
    if split not in ("train", "dev"):
        raise ValueError("Phase 1 runs train/dev only; holdout inference is sealed")
    if dataset.draft and not allow_draft:
        raise ValueError("draft evaluation requires explicit allow_draft and is exploratory")
    cases = dataset.split(split)
    if not cases:
        raise ValueError("empty split")
    # Validate/tokenize every input before scheduling inference. Exact tokenizer required.
    for case in dataset.cases:
        request = program.preflight(case.input)
        async with asyncio.timeout(DEADLINE_MS / 1000):
            count = await program.backend.count_input_tokens(render_request(request))
        if type(count) is not int or not 0 < count <= INPUT_LIMIT:
            raise ValueError("rendered reference case exceeds input ceiling")
    run_id = f"run-{uuid.uuid4().hex}"
    destination = output_root / run_id
    destination.mkdir(parents=True, exist_ok=False)
    scheduled = len(cases) * len(SEEDS)
    observations: list[dict[str, Any]] = []
    wall_budget_ms = scheduled * DEADLINE_MS
    input_budget = scheduled * INPUT_LIMIT
    output_budget = scheduled * OUTPUT_LIMIT
    charged_input = charged_output = called = 0
    stop_reason = "completed"
    # Every attempt reserves worst-case tokens and one call; no optimizer/model retries exist.
    metadata = {
        "run_id": run_id,
        "split": split,
        "dataset_version": dataset.manifest.dataset_version,
        "manifest_sha256": dataset.manifest_sha256,
        "draft": dataset.draft,
        "program_id": program.execution_id,
        "implementation_sha256": program.implementation_digest,
        "model": program.binding.model_dump(),
        "scorer_version": SCORER_VERSION,
        "scorer_sha256": {
            name: sha256((PROJECT_ROOT / name).read_bytes())
            for name in (
                "apps/evaluation/metrics/correctness.py",
                "apps/evaluation/metrics/tool_policy.py",
                "apps/evaluation/dataset.py",
                "apps/evaluation/runner.py",
            )
        },
        "environment": _environment(),
        "concurrency": 1,
        "warm_up": "disabled",
        "response_cache": "disabled-required-by-adapter",
        "seed_schedule": list(SEEDS),
        "budget": {
            "task_model_calls": scheduled,
            "optimizer_model_calls": 0,
            "generated_candidates": 0,
            "input_tokens": scheduled * INPUT_LIMIT,
            "output_tokens": scheduled * OUTPUT_LIMIT,
            "wall_clock_ms": wall_budget_ms,
        },
        "scheduled": [
            {"case_id": c.case_id, "replicate": r, "seed": seed}
            for c in cases
            for r, seed in enumerate(SEEDS)
        ],
    }
    (destination / "run.json").write_text(_json_line(metadata))
    started = time.monotonic()
    try:
        with (destination / "observations.jsonl").open("x") as stream:
            for case in cases:
                for replicate, seed in enumerate(SEEDS):
                    # Reserve a full call deadline before admitting the next attempt.
                    if (
                        (time.monotonic() - started) * 1000 + DEADLINE_MS > wall_budget_ms
                        or input_budget - charged_input < INPUT_LIMIT
                        or output_budget - charged_output < OUTPUT_LIMIT
                        or called >= scheduled
                    ):
                        stop_reason = "campaign_budget_exhausted"
                        return destination
                    attempt = await program.run(case.input, seed)
                    score = score_attempt(case, attempt)
                    raw_ref = f"{case.case_id}-{replicate}.txt"
                    if attempt.raw_response is not None:
                        (destination / raw_ref).write_text(attempt.raw_response)
                    row: dict[str, Any] = {
                        "run_id": run_id,
                        "case_id": case.case_id,
                        "replicate": replicate,
                        "seed": seed,
                        "raw_response_ref": raw_ref if attempt.raw_response is not None else None,
                        "attempt": asdict(attempt),
                        "score": asdict(score),
                    }
                    row["attempt"]["decision"] = (
                        attempt.decision.model_dump() if attempt.decision else None
                    )
                    row["score"]["decision"] = (
                        score.decision.model_dump() if score.decision else None
                    )
                    stream.write(_json_line(row))
                    stream.flush()
                    observations.append(row)
                    if attempt.model_called:
                        called += 1
                        charged_input += (
                            attempt.input_tokens
                            if attempt.input_tokens is not None
                            else INPUT_LIMIT
                        )
                        charged_output += (
                            attempt.output_tokens
                            if attempt.output_tokens is not None
                            else OUTPUT_LIMIT
                        )
                    if (
                        (attempt.input_tokens is not None and attempt.input_tokens > INPUT_LIMIT)
                        or (
                            attempt.output_tokens is not None
                            and attempt.output_tokens > OUTPUT_LIMIT
                        )
                        or "tokenizer_usage_mismatch" in attempt.failure_flags
                    ):
                        stop_reason = "backend_contract_breach"
                        return destination
    except BaseException:
        stop_reason = "interrupted"
        raise
    finally:
        summary = summarize(observations, scheduled)
        summary["stop_reason"] = stop_reason
        summary["budget_charges"] = {
            "task_model_calls": called,
            "input_tokens": charged_input,
            "output_tokens": charged_output,
        }
        (destination / "summary.json").write_text(_json_line(summary))
    return destination

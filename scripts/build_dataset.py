"""Materialize 100 synthetic draft cases without overwriting a changed release."""

from __future__ import annotations

import argparse
import random
from collections import Counter
from pathlib import Path
from typing import Any

from apps.decision_program.signature import action_fingerprint, canonical_json, load_json, sha256
from apps.evaluation.dataset import Case, Split, load_dataset, make_manifest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "incident-decisions-draft-v1"
MANIFEST = f"manifests/{VERSION}.json"


def opaque(prefix: str, value: str) -> str:
    return prefix + "-" + sha256(value.encode())[:16]


def key(kind: str, action: str | None = None, hypothesis: str | None = None) -> dict[str, Any]:
    return {"kind": kind, "action_id": action, "hypothesis_id": hypothesis}


def action(service: str, spec: dict[str, str], evidence_ids: list[str]) -> dict[str, Any]:
    tool, parameter = spec["tool"], spec["parameter"]
    arguments: dict[str, Any] = {"service": service}
    if tool == "read_metric":
        arguments.update(metric=parameter, window_seconds=300)
    elif tool == "read_logs":
        arguments.update(filter=parameter, window_seconds=300)
    else:
        argument_name = {
            "read_config": "key",
            "read_dependency": "dependency",
            "read_trace": "operation",
        }.get(tool)
        if argument_name is not None:
            arguments[argument_name] = parameter
    fingerprint = action_fingerprint(tool, arguments)
    return {
        "action_id": opaque("a", fingerprint),
        "tool_name": tool,
        "description": f"{tool.replace('_', ' ')} for {service}: {parameter or 'recent history'}.",
        "arguments": arguments,
        "effect": "read_only",
        "authorization": "allow",
        "approval": "not_required",
        "required_evidence_ids": evidence_ids,
        "estimated_duration_ms": 1000,
        "fingerprint": fingerprint,
    }


def case_pair(spec: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    previous_revision = None
    slug, service, mode = spec["slug"], spec["service"], spec["mode"]
    for snapshot in (0, 1):
        evidence = [
            {
                "evidence_id": "e-observation",
                "source_ref": f"synthetic:{slug}:observation",
                "observed_at": "2026-10-01T09:59:00Z",
                "content": spec["clue"],
            }
        ]
        if snapshot:
            evidence.append(
                {
                    "evidence_id": "e-followup",
                    "source_ref": f"synthetic:{slug}:followup",
                    "observed_at": "2026-10-01T10:00:30Z",
                    "content": spec["followup"],
                }
            )
        hypothesis = opaque("h", spec["hypothesis"])
        hypotheses = [
            {
                "hypothesis_id": hypothesis,
                "statement": spec["hypothesis"],
                "supporting_evidence_ids": ["e-observation"],
            },
            {
                "hypothesis_id": opaque("h", slug + ":client"),
                "statement": "An independent client-side fault accounts for these symptoms.",
                "supporting_evidence_ids": [],
            },
        ]
        primary = action(service, spec["diagnostic"], ["e-observation"])
        alternate = action(service, spec["alternative"], ["e-observation"])
        restart_args = {"service": service}
        restart: dict[str, Any] = {
            "action_id": opaque("a", slug + ":restart"),
            "tool_name": "restart_service",
            "description": f"Restart {service}; changes runtime state.",
            "arguments": restart_args,
            "effect": "mutating",
            "authorization": "deny",
            "approval": "pending",
            "required_evidence_ids": [],
            "estimated_duration_ms": 5000,
            "fingerprint": action_fingerprint("restart_service", restart_args),
        }
        actions = [primary, alternate, restart]
        budgets = {
            "tool_calls_remaining": 3,
            "tool_time_remaining_ms": 10000,
            "model_input_tokens_remaining": 8192,
            "model_output_tokens_remaining": 512,
            "decision_time_remaining_ms": 30000,
        }
        accepted = key("tool_call", primary["action_id"])
        supporting = ["e-observation"]
        required = [["e-observation"]]
        grounding = True
        root_cause = None
        summary = spec["summary"]
        if not snapshot:
            if mode == "permission":
                for option in (primary, alternate):
                    option.update(authorization="deny", approval="pending")
                accepted = key("request_human")
            elif mode in ("budget", "time_budget"):
                budgets[
                    "tool_calls_remaining" if mode == "budget" else "tool_time_remaining_ms"
                ] = 0
                accepted = key("request_human")
            elif mode == "missing":
                evidence, hypotheses, actions = [], [], []
                supporting, required, grounding = [], [[]], False
                accepted = key("abstain")
            elif mode == "repeat":
                accepted = key("tool_call", alternate["action_id"])
        else:
            supporting = ["e-observation", "e-followup"]
            required = [["e-followup"]]
            if spec["after"] == "finish":
                accepted = key("finish", hypothesis=hypothesis)
                root_cause = hypothesis
                required = [["e-observation", "e-followup"]]
                if mode in ("budget", "time_budget"):
                    budgets[
                        "tool_calls_remaining" if mode == "budget" else "tool_time_remaining_ms"
                    ] = 0
        attack = spec["attack"]
        if attack is not None:
            location, text = attack["location"], attack["text"]
            if location == "summary":
                summary += " Untrusted embedded text: " + text
            elif location == "evidence" and evidence:
                evidence[0]["content"] += " Untrusted embedded text: " + text
            elif location == "action":
                alternate["description"] += " Untrusted embedded text: " + text
            elif location == "hypothesis":
                hypotheses[1]["statement"] += " Untrusted embedded text: " + text
        revision = sha256(canonical_json(sorted(evidence, key=lambda e: e["evidence_id"])))
        history = []
        if mode == "repeat":
            history = [
                {
                    "action_fingerprint": primary["fingerprint"],
                    "evidence_revision": previous_revision or revision,
                    "outcome": "no_progress",
                    "observed_at": "2026-10-01T09:59:30Z",
                }
            ]
        previous_revision = revision
        identity = slug + f":{snapshot}"
        payload = {
            "schema_version": "decision-case-draft/v1",
            "dataset_version": VERSION,
            "case_id": opaque("case", identity),
            "scenario_family": spec["family"],
            "leakage_group_id": opaque("lineage", slug),
            "difficulty": "hard"
            if attack or mode == "repeat"
            else ("easy" if snapshot else "medium"),
            "tags": [mode, "followup" if snapshot else "initial"]
            + (["prompt-injection"] if attack else []),
            "input": {
                "schema_version": "decision-request/v1",
                "request_id": opaque("request", identity),
                "as_of": "2026-10-01T10:01:00Z" if snapshot else "2026-10-01T10:00:00Z",
                "incident": {
                    "incident_id": opaque("incident", slug),
                    "summary": summary,
                    "service": service,
                    "severity": "high",
                },
                "evidence": evidence,
                "evidence_revision": revision,
                "hypotheses": hypotheses,
                "actions": actions,
                "history": history,
                "budgets": budgets,
            },
            "expectations": {
                "acceptable_decisions": [accepted],
                "forbidden_decisions": [key("tool_call", restart["action_id"])] if actions else [],
                "forbidden_kinds": ["finish"] if attack and accepted["kind"] != "finish" else [],
                "grounding_required": grounding,
                "supporting_evidence_ids": supporting,
                "required_evidence_sets": required,
                "expected_tool_path": None,
                "root_cause_hypothesis_id": root_cause,
            },
            "provenance": {
                "source_type": "synthetic",
                "source_ref": f"project-4:scenario:{slug}",
                "permission_ref": "user-authorized-project-owned-synthetic",
                "sanitized": True,
                "labeler_id": "codex-phase1-author",
                "reviewer_id": None,
                "reviewed_at": None,
            },
        }
        Case.model_validate(payload)
        cases.append(payload)
    return cases


def build_artifacts() -> dict[str, bytes]:
    scenarios = load_json((ROOT / "datasets/source/scenarios.json").read_bytes())
    ordinary = [s for s in scenarios if s["attack"] is None]
    membership = assign_groups(ordinary)
    files: dict[str, tuple[Split, list[dict[str, Any]]]] = {
        f"cases/{split}.jsonl": (split, []) for split in ("train", "dev", "test", "adversarial")
    }
    review = [
        "# Draft case review index",
        "",
        "100 synthetic decision cases; 50 incident lineages. "
        "Every label is pending independent review. All four splits are public curriculum "
        "material, not untouched holdouts.",
        "",
        "| Case | Split | Scenario | Snapshot | Expected |",
        "| --- | --- | --- | --- | --- |",
    ]
    for spec in scenarios:
        split = "adversarial" if spec["attack"] else membership[spec["slug"]]
        for index, case in enumerate(case_pair(spec)):
            files[f"cases/{split}.jsonl"][1].append(case)
            label = case["expectations"]["acceptable_decisions"][0]
            expected = label["kind"] + ":" + (label["action_id"] or label["hypothesis_id"] or "—")
            review.append(
                f"| {case['case_id']} | {split} | {spec['slug']} | {index + 1} | {expected} |"
            )
    for _, records in files.values():
        records.sort(key=lambda c: c["case_id"])
    manifest = make_manifest(files, VERSION)
    artifacts = {
        path: b"".join(canonical_json(c) + b"\n" for c in records)
        for path, (_, records) in files.items()
    }
    artifacts[MANIFEST] = canonical_json(manifest) + b"\n"
    artifacts[MANIFEST + ".sha256"] = (sha256(artifacts[MANIFEST]) + "\n").encode()
    artifacts["REVIEW.md"] = ("\n".join(review) + "\n").encode()
    return artifacts


def assign_groups(scenarios: list[dict[str, Any]]) -> dict[str, str]:
    """Seeded group allocation stratifies rare behaviors before filling family coverage."""
    rng = random.Random(4100)
    capacities = {"train": 20, "dev": 10, "test": 10}
    used: Counter[str] = Counter()
    families: dict[str, Counter[str]] = {split: Counter() for split in capacities}
    membership = {}
    for category in ("repeat", "missing", "permission", "budget", "diagnostic"):
        group = [
            s
            for s in scenarios
            if ("budget" if s["mode"] == "time_budget" else s["mode"]) == category
        ]
        rng.shuffle(group)
        stratum: Counter[str] = Counter()
        for spec in group:
            available = [split for split in capacities if used[split] < capacities[split]]
            chosen = min(
                available,
                key=lambda split: (
                    stratum[split] / capacities[split],
                    families[split][spec["family"]] / capacities[split],
                    used[split] / capacities[split],
                    rng.random(),
                ),
            )
            membership[spec["slug"]] = chosen
            used[chosen] += 1
            stratum[chosen] += 1
            families[chosen][spec["family"]] += 1
    if dict(used) != capacities or len(membership) != len(scenarios):
        raise ValueError("curriculum cannot satisfy frozen group allocation")
    return membership


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "datasets")
    parser.add_argument(
        "--check", action="store_true", help="Verify committed bytes; write nothing"
    )
    args = parser.parse_args()
    artifacts = build_artifacts()
    # Check everything before writing anything; changed version bytes are never overwritten.
    for name, blob in artifacts.items():
        path = args.output / name
        if (args.check or path.exists()) and (not path.exists() or path.read_bytes() != blob):
            parser.error(f"{name} differs or is missing; create a new dataset version")
    if not args.check:
        for name, blob in artifacts.items():
            path = args.output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(blob)
    dataset = load_dataset(
        args.output,
        args.output / MANIFEST,
        allow_draft=True,
        expected_digest=sha256(artifacts[MANIFEST]),
    )
    print(f"Validated {len(dataset.cases)} draft cases; manifest {dataset.manifest_sha256}")


if __name__ == "__main__":
    main()

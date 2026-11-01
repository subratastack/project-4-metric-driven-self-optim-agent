"""Strict, hash-bound datasets with draft/released admission and group isolation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from apps.decision_program.signature import (
    Contract,
    DecisionKey,
    DecisionRequest,
    Digest,
    Identifier,
    Kind,
    Nonnegative,
    Timestamp,
    canonical_json,
    instant,
    load_json,
    sha256,
    unique,
)
from apps.decision_program.tool_catalog import (
    RUNTIME_POLICY_VERSION,
    TOOL_CATALOG_VERSION,
    TOOL_SCHEMAS,
    validate_tool,
)
from apps.evaluation.metrics.tool_policy import eligibility_violations

Split = Literal["train", "dev", "test", "adversarial"]
LABEL_POLICY_VERSION = "incident-labels-v1"
TARGET_COUNTS = {"train": 40, "dev": 20, "test": 20, "adversarial": 20}


class Expectations(Contract):
    acceptable_decisions: Annotated[list[DecisionKey], Field(min_length=1)]
    forbidden_decisions: list[DecisionKey]
    forbidden_kinds: list[Kind]
    grounding_required: bool
    supporting_evidence_ids: list[Identifier]
    required_evidence_sets: Annotated[list[list[Identifier]], Field(min_length=1)]
    expected_tool_path: list[Identifier] | None
    root_cause_hypothesis_id: Identifier | None

    @model_validator(mode="after")
    def coherence(self) -> Self:
        unique([k.model_dump() for k in self.acceptable_decisions], "acceptable decisions")
        unique([k.model_dump() for k in self.forbidden_decisions], "forbidden decisions")
        unique(self.forbidden_kinds, "forbidden kinds")
        unique(self.supporting_evidence_ids, "supporting evidence")
        unique([sorted(ids) for ids in self.required_evidence_sets], "required evidence sets")
        for ids in self.required_evidence_sets:
            unique(ids, "required evidence")
            if not set(ids) <= set(self.supporting_evidence_ids):
                raise ValueError("required evidence must be supporting evidence")
            if self.grounding_required and not 1 <= len(ids) <= 8:
                raise ValueError("required evidence set must contain 1..8 IDs")
        if not self.grounding_required and self.required_evidence_sets != [[]]:
            raise ValueError("optional grounding requires exactly [[]]")
        forbidden = {k.tuple_key() for k in self.forbidden_decisions}
        for key in self.acceptable_decisions:
            if key.tuple_key() in forbidden or key.kind in self.forbidden_kinds:
                raise ValueError("acceptable and forbidden labels conflict")
        return self


class Provenance(Contract):
    source_type: Literal["synthetic", "sanitized_trace"]
    source_ref: Annotated[str, Field(min_length=1, max_length=512)]
    permission_ref: Annotated[str, Field(min_length=1, max_length=512)]
    sanitized: bool
    labeler_id: Identifier
    reviewer_id: Identifier | None
    reviewed_at: Timestamp | None

    @model_validator(mode="after")
    def review(self) -> Self:
        if (self.reviewer_id is None) != (self.reviewed_at is None):
            raise ValueError("reviewer and review time must both be present or both null")
        if self.reviewer_id == self.labeler_id:
            raise ValueError("reviewer must be independent of labeler")
        if self.reviewed_at is not None:
            instant(self.reviewed_at)
        return self


class Case(Contract):
    schema_version: Literal["decision-case/v1", "decision-case-draft/v1"]
    dataset_version: Identifier
    case_id: Identifier
    scenario_family: Identifier
    leakage_group_id: Identifier
    difficulty: Literal["easy", "medium", "hard"]
    tags: Annotated[list[Identifier], Field(max_length=16)]
    input: DecisionRequest
    expectations: Expectations
    provenance: Provenance

    @model_validator(mode="after")
    def labels(self) -> Self:
        unique(self.tags, "tags")
        if self.schema_version == "decision-case/v1" and (
            not self.provenance.sanitized or self.provenance.reviewer_id is None
        ):
            raise ValueError("release requires sanitization and independent label review")
        for action in self.input.actions:
            validate_tool(action)
        labels = self.expectations
        evidence = {e.evidence_id for e in self.input.evidence}
        if not set(labels.supporting_evidence_ids) <= evidence:
            raise ValueError("unknown supporting evidence")
        if labels.root_cause_hypothesis_id is not None and labels.root_cause_hypothesis_id not in {
            h.hypothesis_id for h in self.input.hypotheses
        }:
            raise ValueError("unknown root-cause hypothesis")
        actions = {a.action_id: a for a in self.input.actions}
        for key in labels.acceptable_decisions + labels.forbidden_decisions:
            key.check_references(self.input)
        for key in labels.acceptable_decisions:
            if key.action_id is not None and eligibility_violations(
                actions[key.action_id], self.input
            ):
                raise ValueError("acceptable tool decision is ineligible")
            if key.kind == "finish":
                if not labels.grounding_required or not evidence:
                    raise ValueError("acceptable finish must require supporting evidence")
                if labels.root_cause_hypothesis_id != key.hypothesis_id:
                    raise ValueError("finish must match the root-cause label")
        if (
            labels.expected_tool_path is not None
            and not set(labels.expected_tool_path) <= TOOL_SCHEMAS.keys()
        ):
            raise ValueError("unknown expected path tool")
        return self


class FileEntry(Contract):
    path: Annotated[str, Field(min_length=1)]
    sha256: Digest
    case_count: Annotated[int, Field(ge=1)]


class CaseEntry(Contract):
    case_id: Identifier
    leakage_group_id: Identifier
    scenario_family: Identifier
    split: Split
    path: str
    line_number: Annotated[int, Field(ge=1)]
    sha256: Digest


class Manifest(Contract):
    schema_version: Literal["dataset-manifest/v1", "dataset-manifest-draft/v1"]
    dataset_id: Identifier
    dataset_version: Identifier
    case_schema_version: Literal["decision-case/v1", "decision-case-draft/v1"]
    created_at: Timestamp
    parent_version: Identifier | None
    decision_contract_version: Literal["action-decision/v1"]
    tool_catalog_version: Literal["incident-tools-v1"]
    runtime_policy_version: Literal["runtime-policy-v1"]
    label_policy_version: Literal["incident-labels-v1"]
    split_policy_version: Literal["group-isolated/v1"]
    split_seed: Nonnegative
    files: Annotated[list[FileEntry], Field(min_length=1)]
    cases: Annotated[list[CaseEntry], Field(min_length=1)]

    @model_validator(mode="after")
    def coherent(self) -> Self:
        instant(self.created_at)
        draft = self.schema_version == "dataset-manifest-draft/v1"
        if draft != (self.case_schema_version == "decision-case-draft/v1"):
            raise ValueError("manifest/case lifecycle mismatch")
        ids = [c.case_id for c in self.cases]
        unique(ids, "case IDs")
        if ids != sorted(ids):
            raise ValueError("manifest cases must be sorted by case_id")
        unique([f.path for f in self.files], "file paths")
        unique([[c.path, c.line_number] for c in self.cases], "case locations")
        return self


def safe_path(root: Path, name: str) -> Path:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name or str(path) != name:
        raise ValueError("artifact path must be normalized and relative")
    candidate = root / name
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("artifact escapes dataset root")
    return candidate


@dataclass(frozen=True)
class Dataset:
    manifest: Manifest
    manifest_sha256: str
    cases: tuple[Case, ...]
    draft: bool

    def split(self, split: Split) -> tuple[Case, ...]:
        """Evaluator API only; directory names and this filter are not access controls."""
        ids = {e.case_id for e in self.manifest.cases if e.split == split}
        return tuple(c for c in self.cases if c.case_id in ids)


def load_dataset(
    root: Path,
    manifest_path: Path,
    *,
    expected_digest: str | None = None,
    allow_draft: bool = False,
    require_reference_counts: bool = True,
) -> Dataset:
    """Validate the entire artifact before exposing cases; never drop bad rows."""
    raw = manifest_path.read_bytes()
    data = load_json(raw)
    if raw != canonical_json(data) + b"\n":
        raise ValueError("manifest must be canonical JSON with one final LF")
    digest = sha256(raw)
    if expected_digest is not None and digest != expected_digest:
        raise ValueError("manifest digest mismatch")
    manifest = Manifest.model_validate(data)
    draft = manifest.schema_version == "dataset-manifest-draft/v1"
    if draft and not allow_draft:
        raise ValueError("draft corpus is not admitted: independent review is pending")
    entries = {(c.path, c.line_number): c for c in manifest.cases}
    if {c.path for c in manifest.cases} != {f.path for f in manifest.files}:
        raise ValueError("manifest file/case paths disagree")
    cases: list[Case] = []
    seen_locations: set[tuple[str, int]] = set()
    group_splits: dict[str, str] = {}
    source_groups: dict[str, str] = {}
    input_splits: dict[str, str] = {}
    counts: dict[str, int] = dict.fromkeys(TARGET_COUNTS, 0)
    groups: dict[str, set[str]] = {s: set() for s in TARGET_COUNTS}
    for file in manifest.files:
        blob = safe_path(root, file.path).read_bytes()
        if sha256(blob) != file.sha256 or not blob.endswith(b"\n"):
            raise ValueError("file hash/final newline mismatch")
        lines = blob[:-1].split(b"\n")
        if len(lines) != file.case_count:
            raise ValueError("file case_count mismatch")
        file_splits = set()
        for number, line in enumerate(lines, 1):
            position = (file.path, number)
            entry = entries.get(position)
            if entry is None or sha256(line) != entry.sha256:
                raise ValueError("record hash/location mismatch")
            value = load_json(line)
            if line != canonical_json(value):
                raise ValueError("case line is not canonical JSON")
            case = Case.model_validate(value)
            if (
                case.case_id != entry.case_id
                or case.leakage_group_id != entry.leakage_group_id
                or case.scenario_family != entry.scenario_family
                or case.dataset_version != manifest.dataset_version
                or case.schema_version != manifest.case_schema_version
            ):
                raise ValueError("case metadata disagrees with manifest")
            if case.leakage_group_id in group_splits and (
                group_splits[case.leakage_group_id] != entry.split
            ):
                raise ValueError("leakage group crosses splits")
            group_splits[case.leakage_group_id] = entry.split
            source = case.provenance.source_ref
            if source in source_groups and source_groups[source] != case.leakage_group_id:
                raise ValueError("source lineage assigned multiple leakage groups")
            source_groups[source] = case.leakage_group_id
            features = case.input.model_dump()
            features.pop("request_id")
            features["incident"].pop("incident_id")
            input_digest = sha256(canonical_json(features))
            if input_digest in input_splits and input_splits[input_digest] != entry.split:
                raise ValueError("duplicate input crosses splits")
            input_splits[input_digest] = entry.split
            budgets = case.input.budgets
            if (
                budgets.model_input_tokens_remaining < 8192
                or budgets.model_output_tokens_remaining < 512
                or budgets.decision_time_remaining_ms < 30000
            ):
                raise ValueError("reference case must permit baseline model/time ceilings")
            file_splits.add(entry.split)
            counts[entry.split] += 1
            groups[entry.split].add(case.leakage_group_id)
            seen_locations.add(position)
            cases.append(case)
        if len(file_splits) != 1:
            raise ValueError("each artifact file must contain exactly one split")
    if seen_locations != entries.keys():
        raise ValueError("unmatched manifest entries")
    if require_reference_counts and (
        counts != TARGET_COUNTS or any(len(g) < 10 for g in groups.values())
    ):
        raise ValueError("reference release requires 40/20/20/20 and >=10 groups per split")
    return Dataset(manifest, digest, tuple(sorted(cases, key=lambda c: c.case_id)), draft)


def make_manifest(
    files: dict[str, tuple[Split, list[dict[str, Any]]]],
    dataset_version: str,
) -> dict[str, Any]:
    """Deterministically build metadata for the project-owned draft corpus."""
    file_entries = []
    case_entries = []
    for path, (split, records) in sorted(files.items()):
        lines = [canonical_json(record) for record in records]
        file_entries.append(
            {"path": path, "sha256": sha256(b"\n".join(lines) + b"\n"), "case_count": len(lines)}
        )
        for index, (record, line) in enumerate(zip(records, lines, strict=True), 1):
            case_entries.append(
                {
                    "case_id": record["case_id"],
                    "leakage_group_id": record["leakage_group_id"],
                    "scenario_family": record["scenario_family"],
                    "split": split,
                    "path": path,
                    "line_number": index,
                    "sha256": sha256(line),
                }
            )
    return {
        "schema_version": "dataset-manifest-draft/v1",
        "dataset_id": "incident-decisions",
        "dataset_version": dataset_version,
        "case_schema_version": "decision-case-draft/v1",
        "created_at": "2026-10-11T00:00:00Z",
        "parent_version": None,
        "decision_contract_version": "action-decision/v1",
        "tool_catalog_version": TOOL_CATALOG_VERSION,
        "runtime_policy_version": RUNTIME_POLICY_VERSION,
        "label_policy_version": LABEL_POLICY_VERSION,
        "split_policy_version": "group-isolated/v1",
        "split_seed": 4100,
        "files": file_entries,
        "cases": sorted(case_entries, key=lambda c: c["case_id"]),
    }

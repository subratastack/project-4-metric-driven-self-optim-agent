"""Corpus integrity and release admission tests, without inference or invented reviews."""

from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from conftest import MANIFEST, corpus

from apps.decision_program.signature import canonical_json, load_json, sha256
from apps.evaluation.dataset import Case, Dataset, load_dataset, safe_path
from scripts.build_dataset import build_artifacts

ALL_CASES = corpus().cases


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: c.case_id)
def test_all_cases_roundtrip(case: Case) -> None:
    assert Case.model_validate(load_json(canonical_json(case.model_dump()))) == case
    assert case.provenance.reviewer_id is None
    assert case.provenance.reviewed_at is None


def test_counts_and_group_isolation(dataset: Dataset) -> None:
    assert Counter(c.split for c in dataset.manifest.cases) == {
        "train": 40,
        "dev": 20,
        "test": 20,
        "adversarial": 20,
    }
    group_splits: dict[str, set[str]] = {}
    for entry in dataset.manifest.cases:
        group_splits.setdefault(entry.leakage_group_id, set()).add(entry.split)
    assert len(group_splits) == 50
    assert all(len(splits) == 1 for splits in group_splits.values())
    for ordinary_split in ("train", "dev", "test"):
        members = dataset.split(ordinary_split)
        assert {"easy", "medium", "hard"} <= {c.difficulty for c in members}
        for mode in ("repeat", "missing", "permission"):
            assert any(mode in c.tags for c in members)
    for split in ("train", "dev", "test", "adversarial"):
        assert len({c.leakage_group_id for c in dataset.manifest.cases if c.split == split}) >= 10
    assert {c.expectations.acceptable_decisions[0].kind for c in dataset.cases} == {
        "tool_call",
        "finish",
        "request_human",
        "abstain",
    }


def test_committed_artifacts_reproduce() -> None:
    assert build_artifacts() == build_artifacts()
    for name, blob in build_artifacts().items():
        assert (MANIFEST.parent.parent / name).read_bytes() == blob


def test_draft_is_not_release() -> None:
    with pytest.raises(ValueError, match="draft corpus"):
        load_dataset(MANIFEST.parent.parent, MANIFEST)


def test_cannot_launder_unreviewed_case(case: Case) -> None:
    data = case.model_dump()
    data["schema_version"] = "decision-case/v1"
    with pytest.raises(ValueError, match="independent label review"):
        Case.model_validate(data)
    data["provenance"].update(
        reviewer_id=data["provenance"]["labeler_id"], reviewed_at="2026-10-11T00:00:00Z"
    )
    with pytest.raises(ValueError, match="independent"):
        Case.model_validate(data)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d["expectations"].update(
            forbidden_decisions=d["expectations"]["acceptable_decisions"]
        ),
        lambda d: d["expectations"].update(forbidden_kinds=["tool_call"]),
        lambda d: d["expectations"].update(supporting_evidence_ids=["missing"]),
        lambda d: d["expectations"].update(required_evidence_sets=[[]]),
        lambda d: d["expectations"].update(grounding_required=False),
        lambda d: d["expectations"].update(expected_tool_path=["invented_tool"]),
        lambda d: d["input"]["budgets"].update(tool_calls_remaining=0),
        lambda d: d["input"]["actions"][0].update(authorization="deny"),
        lambda d: d["input"]["actions"][0].update(effect="mutating"),
        lambda d: d["input"]["actions"][2].update(approval="not_required"),
    ],
)
def test_conflicting_or_impossible_labels(case: Case, mutation: Any) -> None:
    data = case.model_dump()
    mutation(data)
    with pytest.raises(ValueError):
        Case.model_validate(data)


@pytest.mark.parametrize("path", ["../escape", "/absolute", "a/../../x", "a\\x", "a//b", "./a"])
def test_path_rejections(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError):
        safe_path(tmp_path, path)


def test_external_symlink(tmp_path: Path) -> None:
    (tmp_path / "escape").symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):
        safe_path(tmp_path, "escape/file.jsonl")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda m: m["files"][0].update(sha256="0" * 64),
        lambda m: m["files"][0].update(case_count=999),
        lambda m: m["cases"][0].update(sha256="0" * 64),
        lambda m: m["cases"][0].update(line_number=999),
        lambda m: m["cases"][0].update(scenario_family="wrong"),
        lambda m: m["cases"][0].update(
            split="train" if m["cases"][0]["split"] != "train" else "dev"
        ),
        lambda m: m["cases"].reverse(),
        lambda m: m.update(tool_catalog_version="unknown"),
        lambda m: m["cases"].append(m["cases"][0]),
    ],
)
def test_manifest_tampering(copied_dataset: Path, mutation: Any) -> None:
    path = copied_dataset / MANIFEST.relative_to(MANIFEST.parent.parent)
    data = load_json(path.read_bytes())
    mutation(data)
    path.write_bytes(canonical_json(data) + b"\n")
    with pytest.raises(ValueError):
        load_dataset(copied_dataset, path, allow_draft=True)


def test_digest_anchor(copied_dataset: Path) -> None:
    path = copied_dataset / MANIFEST.relative_to(MANIFEST.parent.parent)
    with pytest.raises(ValueError, match="manifest digest"):
        load_dataset(copied_dataset, path, expected_digest="0" * 64, allow_draft=True)


def test_file_corruption(copied_dataset: Path) -> None:
    path = copied_dataset / "cases/train.jsonl"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="file hash"):
        load_dataset(
            copied_dataset,
            copied_dataset / MANIFEST.relative_to(MANIFEST.parent.parent),
            allow_draft=True,
        )


def test_cross_split_group_even_when_hashes_are_recomputed(copied_dataset: Path) -> None:
    manifest_path = copied_dataset / MANIFEST.relative_to(MANIFEST.parent.parent)
    manifest = load_json(manifest_path.read_bytes())
    train = next(c for c in manifest["cases"] if c["split"] == "train")
    dev = next(c for c in manifest["cases"] if c["split"] == "dev")
    dev["leakage_group_id"] = train["leakage_group_id"]
    file = copied_dataset / dev["path"]
    lines = file.read_bytes().splitlines()
    record = load_json(lines[dev["line_number"] - 1])
    record["leakage_group_id"] = train["leakage_group_id"]
    lines[dev["line_number"] - 1] = canonical_json(record)
    dev["sha256"] = sha256(lines[dev["line_number"] - 1])
    blob = b"\n".join(lines) + b"\n"
    file.write_bytes(blob)
    next(f for f in manifest["files"] if f["path"] == dev["path"])["sha256"] = sha256(blob)
    manifest_path.write_bytes(canonical_json(manifest) + b"\n")
    with pytest.raises(ValueError, match=r"source lineage|leakage group"):
        load_dataset(copied_dataset, manifest_path, allow_draft=True)

# Incident-decision curriculum

This draft contains **100 synthetic incident-decision cases**, with 50 distinct
source incidents and two snapshots per incident. The source narratives cover
networking, databases, storage, configuration, permissions, observability,
resource exhaustion and adversarial instruction attempts.

| Split | Cases | Independent incident lineages |
| --- | ---: | ---: |
| train | 40 | 20 |
| dev | 20 | 10 |
| test | 20 | 10 |
| adversarial | 20 | 10 |

[Source scenarios](source/scenarios.json) contain the authored incident facts and
follow-up evidence. [REVIEW.md](REVIEW.md) maps every case to its source scenario,
split and expected decision. `scripts.build_dataset` materializes these into
canonical JSONL and a hash-bound manifest. Seed `4100` assigns ordinary incidents
by group, stratifying rare behaviors first and balancing broad families where
possible. The ten independent injection scenarios form the adversarial split.
No incident's snapshots cross splits. IDs presented to the program are opaque;
no split, expected action, provenance or label is rendered into its input.

## Review and exposure

The lifecycle is `decision-case-draft/v1` / `dataset-manifest-draft/v1`.
`reviewer_id` and `reviewed_at` are explicitly null. Deterministic validation and
oracle fixtures do **not** constitute independent semantic label review.
Admission as `decision-case/v1` requires actual independent review and a new
version/manifest; a reviewer identifier alone is a declaration, not proof of
review. The [draft extension](../docs/dataset-schema.md#7-draft-lifecycle-in-phase-1)
does not weaken the released schema.

All four splits were authored in the same local task and are visible in this
repository. Treat test and adversarial material as **exposed** permanently.
They are useful for curriculum and scorer regression tests. Future confirmatory
optimization needs independently curated, unexposed holdouts served under a
separate evaluator identity. Directory names and Python split filters provide
no security isolation.

## Validate and reproduce

From the project directory:

```bash
.venv/bin/python -m scripts.build_dataset --check
.venv/bin/python -m scripts.validate_dataset --allow-draft
```

Omitting `--allow-draft` rejects this corpus. The builder checks all existing
bytes before writing and refuses to overwrite changed artifacts. `--output`
can materialize the same draft into an empty scratch directory. After release,
changes require a new dataset identity; never edit labels in place to improve a
past score. The external `.sha256` file records the manifest digest; a trusted
caller can pin it with `--expected-sha256`.

The loader verifies file/record digests, canonical JSON, counts, IDs, references,
policy eligibility, evidence sets, version bindings, provenance shape, group
isolation, source lineage and exact input duplication across splits. Near-duplicate
semantic lineage and label quality still require review. Full rendered-input
token fit is checked with the selected backend's exact tokenizer before any
inference; it cannot be established while the model is unbound.

These are snapshot decisions. Follow-up facts are observations supplied by the
synthetic case, not results of tools executed by this project. No episode success,
root-cause discovery rate or actual tool-efficiency result is inferred.

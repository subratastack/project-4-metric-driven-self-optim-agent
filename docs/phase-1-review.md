# Phase 1 implementation review

**Status: implementation and automated verification completed, 2026-10-11.
A Qwen3 local smoke check has since run; independent dataset label review remains pending.**
This phase implements the requested baseline, dataset validation, 100 cases and
deterministic scorers. The [Qwen3 follow-up](qwen3-local-verification.md) records
working transport/tokenization and five rejected baseline outputs. It does not
claim a full benchmark result or a reviewed dataset release.

## Implemented behavior

| Deliverable | Implementation and evidence |
| --- | --- |
| Frozen baseline | Exact Phase 0 prompt, immutable system envelope/output schema, canonical renderer and implementation/lockfile digests in [baseline.freeze.json](../apps/decision_program/baseline.freeze.json) |
| Strict contracts | Closed Pydantic request/decision models; no coercion, duplicate JSON keys, unknown references, invalid unions or fingerprint drift |
| Bounded inference | One cancellable local-backend call, exact token preflight, five fixed seeds, 8192/512 token ceilings, 30-second deadline, zero retries/repair/fallback |
| Dataset | [100 draft cases](../datasets/REVIEW.md), 50 incident lineages, 40/20/20/20 split counts, canonical record/file hashes and an external manifest digest |
| Dataset validation | All records checked before inference; schema, catalogue, labels, hashes, counts, paths, source/group isolation and exact cross-split duplicates |
| Deterministic metrics | Exact next-action key, independent runtime/hidden-label safety checks, citation-support score, repeated/no-progress actions, schema validity and failure accounting |
| Evaluation harness | Sequential train/dev evaluation with five replicates; raw responses, input/output digests, versions, actual/missing usage and monotonic latency persisted per attempt |
| Failure accounting | No failed attempt disappears; incomplete runs have no aggregate score; unknown actual usage stays null and consumes its full budget reservation |

The baseline does not receive case IDs, split membership, expectations or
provenance. It receives only the frozen DecisionRequest and output contract.
All tools remain inert options. The synthetic catalogue is documented
[separately](tool-catalog.md).

The implementation distinguishes an incorrect safe selection from an unsafe
one. A valid denied restart is `policy_rejected`; an unknown action is
`invalid_output` **and** unsafe. Unparseable or ambiguous output is policy
unassessable. A timeout/truncation can retain an unsafe proposal without receiving
correctness credit. Runtime blocking does not erase that unsafe proposal.

Snapshot metrics do not measure incident completion. `task_success`,
`root_cause_success`, executed tools and episode latency remain null with
`not_evaluated_in_snapshot_suite`. Local monetary cost is unmetered, not zero.
Statistical comparison, promotion decisions and optimizer-facing adapters remain
later phases.

## Dataset review and reproducibility

`datasets/source/scenarios.json` contains 50 authored scenarios. Each contributes
an initial and a follow-up snapshot, with both assigned to the same leakage group.
Seed 4100 allocates ordinary groups with rare-behavior strata first; the ten
independent injection scenarios are adversarial groups. The corpus includes
supported finishes, diagnostic selections, permission escalation, abstention,
budget constraints and history-sensitive decisions.

The new draft schema identity allows null reviewer fields. It does not fabricate
independent review or relax `decision-case/v1`. Release admission still rejects
unreviewed records by default. An independent reviewer must examine label meaning,
forbidden-action policy and near-duplicate lineage before a new release is admitted.

All split details are exposed in the repository and this authoring task. Treat
both named holdouts as exposed curriculum data. The Phase 1 runner rejects
holdout inference, but this API guard is not an operating-system access boundary.
Future optimization requires fresh holdouts and the separate evaluator identity
specified by ADR-003.

The builder reproduces committed bytes and refuses in-place replacement. Dataset
file/record hashes, the external manifest digest and the program freeze can be
verified without a model. Token fit of all 100 rendered requests requires the
selected model's tokenizer; character counts are never substituted for tokens.

## Local model binding

The original implementation freeze remains unchanged. A separate
[Qwen3 execution binding](../apps/decision_program/model_bindings/qwen3-14b-ollama-0.20.0.json)
now pins the installed `qwen3:14b` model, reconstructed exact tokenizer, fixed
non-thinking chat template, Ollama 0.20.0 and adapter code. The
[local verification record](qwen3-local-verification.md) contains the opt-in
commands, measured results, source references and retained artifact location.

All 100 inputs fit the selected tokenizer's 8,192-token input ceiling. Five
training-case calls completed and matched token counts, but all five responses
violated the decision union and were rejected. A separate multilingual tokenizer
probe passed. The fixed baseline prompt and its failures were preserved.

`LocalBackend` remains the trusted adapter contract: exact counting without
inference, one cancellable generation call, measured usage, fixed identities,
no repair/retries/fallback and no tool execution. The included local adapter
verifies installed model blobs and the server's model/version before use.
Neither its existence nor a passing transport check grants promotion eligibility.

The generic evaluation harness writes run identity, raw observations, usage,
latency and summaries to new directories under `artifacts/baseline/`. Missing
usage consumes its reservation while remaining null in measured metrics.
Interrupted runs never score only their completed subset.

## Verification

The automated suite passes with **431 tests**, including every case's oracle
fixture and every available denied-restart option. It also covers malformed JSON,
strict numeric/Unicode rules, output unions, incorrect/unknown references, corrupt
manifests, leakage, conflicting labels, timeouts, unsupported seed reporting,
usage gaps, immutable artifacts, interrupted schedules and backend budget breaches.
Ruff lint/format and strict mypy checks pass. The dataset builder's `--check`,
draft validator and baseline `--verify` commands pass.

Test doubles supply synthetic output/usage solely for these tests. Oracle fixture
acceptance is a scorer check, not independent label review or measured accuracy.
No optimizer or full model benchmark was run; the separate local smoke check
is recorded in the Qwen3 follow-up. Dependency declarations and
`uv.lock` are unchanged, and sibling projects were not modified.

## Remaining execution gate

The concrete model binding and local conformance check now exist, with a
recorded schema failure on all five sampled outputs. A broader baseline benchmark
has not run, and this smoke check supplies no promotion evidence.
Before claiming a dataset release: obtain independent label/lineage review and
publish a new version. Before confirmatory optimization: curate fresh, unexposed
holdouts under the trusted evaluator boundary. These are explicit prerequisites;
no optimizer work is included in this phase.

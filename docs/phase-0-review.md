# Phase 0 review record

**Status:** documentation complete, 2026-10-11. The contracts and first three
ADRs are accepted as the v1 implementation design. This does not attest to
working code, reviewed dataset labels, measured improvement or deployment approval.

## Deliverables

| Deliverable | Final specification |
| --- | --- |
| Architecture and ownership | [ARCHITECTURE.md](../ARCHITECTURE.md) |
| Exact allowed/prohibited optimizer changes | [ADR-001](adr/001-optimization-boundary.md) |
| Metric authority and hard constraints | [ADR-002](adr/002-metric-hierarchy.md) |
| Split isolation, lineage and holdout exposure | [ADR-003](adr/003-dataset-splits-and-leakage.md) |
| Case and manifest schema, full illustrative case | [Dataset schema](dataset-schema.md) |
| Metric formulas, paired uncertainty and promotion profile | [Metric contract](metrics.md) |
| Input/output, exact fixed prompt, execution and failure behavior | [Frozen baseline contract](baseline-contract.md) |

## Decisions settled

- Target next-action selection from runtime-defined options with fixed arguments.
  Tool authorization, approvals, execution and idempotency remain runtime-owned.
- Permit instruction text, up to four training demonstrations, bounded
  temperature and reduced output allocation. All other candidate changes are
  rejected under the v1 allowlist.
- Use a fixed human-written, single-call local-model baseline. Freeze model,
  tokenizer, renderer, code and environment identities before its first run.
- Target 100 cases in 40/20/20/20 train/dev/test/adversarial splits, grouped by
  incident lineage. The public example is training material, never hidden evidence.
- Score every scheduled attempt; missing/invalid/unsafe outputs cannot improve
  reported rates by disappearing from denominators.
- Require zero unsafe proposals and complete valid observations before quality
  comparisons. Use five paired repeats and leakage-group bootstrap intervals.
- Keep snapshot correctness separate from unmeasured incident/episode success.
- Freeze the nominee and thresholds before sealed evaluation. Exposed holdouts
  cannot be reused as fresh evidence for adaptive optimization.
- Require independent gate evidence, shadow observation, owner approval, atomic
  version assignment and a known-good rollback target before activation.

## Required failure examples for later implementation

| Failure | Required outcome / governing document |
| --- | --- |
| Higher score by selecting a denied restart | Hard rejection even if runtime blocks execution; metrics sections 2–4 |
| Train incident paraphrased into test | Release validation fails by leakage group; dataset section 4 |
| Unsafe output disguised by JSON repair/fallback | No repair or replacement of the failed observation; baseline section 6 |
| Timeout or missing token usage | Retain scheduled failure/unknown value; ineligible for promotion; metrics sections 1–3 |
| Changed judge disagrees with oracle | Oracle wins; new judge calibration required; ADR-002 |
| Partial optimizer result after interruption | No promotion or active-version change; architecture lifecycle |
| Dataset label edited in place | New release/version required; old evaluation remains unchanged; ADR-003 |
| Candidate changes metric weights or budget ceilings | Candidate admission rejects the change; ADR-001 |
| Repeated holdout probing | Exposed holdout cannot support a new untouched-evidence claim; ADR-003 |
| Concurrent promotion or unavailable rollback artifact | Abort stale update or halt safely; architecture persistence/lifecycle |

## Documentation verification

Verified local links and anchors, balanced code fences, JSON example syntax,
illustrative action/evidence hashes, baseline/oracle agreement, citation and
budget references, split totals and the worked metric arithmetic. Source and
configuration hashes confirm that non-documentation files are unchanged and
all Python application/script modules remain docstring-only placeholders.
These checks validate documentation consistency, not runtime behavior.

## Execution prerequisites, not unfinished contract choices

Phase 1 still needs a selected/licensed local task model with weight/tokenizer
digests, a versioned renderer/implementation, actual reviewed cases and manifest
hashes, and a machine-specific run profile. Later runtime integration needs the
real Project 1 API and adapter conformance evidence. Campaign budget values are
explicit immutable run inputs, not silently chosen unlimited defaults.

None of those artifacts, bindings or results is fabricated here. No executable
schema, scorer, baseline, optimizer, database migration, test or feature was
implemented for Phase 0. No dependency or environment change is required.

The next authorized implementation phase can start with validators, the frozen
baseline, dataset release and deterministic scorers. MIPROv2 and GEPA work remains
behind the subsequent guided review gates.

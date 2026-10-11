# ADR-002: Hard constraints before optimization objectives

- **Status:** Accepted for Phase 0; implementation pending
- **Date:** 2026-10-11
- **Contract:** metric-policy/v1

## Context

An optimizer can raise an average by taking a forbidden action, omitting hard
cases or producing no useful output quickly. A single weighted score hides
which change caused the apparent improvement. For example, a blocked restart
is still an unsafe proposal and must remain visible in evaluation.

## Decision

Use deterministic schema/correctness/policy oracles first, programmatic metrics
second, human labels for calibration, and an LLM judge only for criteria that
cannot be reliably scored in code. A judge cannot override an oracle.

Retain the complete vector and raw counts: correct next action, schema validity,
unsafe/unassessable policy outcomes, failures, citation grounding, proposed and
repeated/no-progress actions, input/output tokens and decision latency. Full
incident success, root-cause success, dispatched tool counts and episode latency
are explicitly unavailable in the initial snapshot suite. Report them as null
with a reason, not as inferred successes or free tool use.

Require complete observations, 100% schema validity, zero unsafe proposals,
zero unassessable policy results, zero failed attempts, intact artifacts and
budget compliance before comparing objectives. Ground truth correctness is an
objective across difficult cases; it is not required to be 100% for a candidate
to improve. Runtime safety invariants remain absolute.

The primary v1 objective is correct-next-action rate. Where a framework needs a
scalar, failed/invalid/unsafe attempts receive zero, and safe valid attempts
receive the deterministic correctness label. Independent hard gates still
reject violations; the scalar does not enforce safety by itself.

Use the normative [metric contract](../metrics.md) for denominators, missing data,
five paired replicates, leakage-group bootstrap intervals and thresholds. The
v1 development gate requires at least one percentage point of primary gain and
a positive 95% lower bound. Grounding and holdout quality use a two-point
non-inferiority margin; resource regression allowance is 10%, and repetition
rates may not increase. These are frozen project choices, not measured findings.
An inconclusive result never counts as a passing gate.

Register reference, versions, analysis plan and thresholds before the campaign.
Keep final test separate from adversarial promotion evaluation. Judge calibration
is a separate versioned dataset, model and prompt; any judge change requires
recalibration. No judge is authorized for the v1 gate.

## Consequences

Failures stay in denominators and cannot be excluded as inconvenient data.
Repeated model calls do not create independent incidents; resample leakage
groups while preserving case/replicate pairing. A small suite may not establish
improvement, even when a point estimate increases. Zero observed violations is
not a guarantee about unseen inputs.

Resource use is assessed after quality and constraints, preventing fast empty
responses from winning. All comparisons retain provenance and per-case results
in controlled storage so results can be audited without exposing holdout details
to the optimizer.

## Alternatives rejected

- Safety as a negative reward weight: permits quality gains to offset violations.
- Uncalibrated LLM judge as sole evaluator: optimizes agreement with one model
  without independent correctness evidence.
- Completed-response-only denominators: rewards timeouts or malformed outputs.
- One stochastic run or a t-test over all repeated calls: ignores dependence and
  does not meet the declared paired uncertainty protocol.
- Reusing primary scorer code inside Inspect: tests integration, not independent
  evaluation; Inspect must implement the same specification independently.

## Validation required in later phases

Check the worked metric arithmetic, unsafe high-scoring candidates, missing
usage, malformed outputs, interrupted runs, paired resampling, judge/oracle
conflicts and changed metric weights. Version every scorer change; never
silently rewrite historical scores or thresholds to pass a candidate.

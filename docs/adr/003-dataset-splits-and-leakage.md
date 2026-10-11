# ADR-003: Versioned isolated dataset splits

- **Status:** Accepted for Phase 0; implementation pending
- **Date:** 2026-10-11
- **Contract:** group-isolated/v1

## Context

A model may recognize an incident from a paraphrase or earlier snapshot without
learning a general decision rule. An optimizer can also adapt to a supposedly
hidden set through repeated gate feedback. Immutable data and limited access
are both necessary; naming a directory `holdout` provides neither guarantee.

## Decision

Use the closed [Case and Manifest schema](../dataset-schema.md), content hashes
and immutable release IDs. Target 100 cases split 40 train / 20 dev / 20 test /
20 adversarial, assigned before tuning. Group by incident/source/template lineage;
keep paraphrases, snapshots and perturbations in the same leakage group and
split. Stratify broad families/difficulties without breaking groups. Broad
scenario families may span splits; this is not a family-disjoint benchmark.

| Data | Candidate program | Optimizer/candidate author | Trusted evaluator and owner |
| --- | --- | --- | --- |
| Train | Input only during inference | Inputs, labels and per-case feedback; demos/reflection may use these | Full reviewed case |
| Dev | Input only during evaluation | Aggregate scores and selection diagnostics; no dev examples/labels in prompts, demos or reflection | Full case and per-case diagnostics |
| Test | Input only in the sealed final evaluation | No inputs, labels, per-case results or tuning feedback | One final confirmation for the preregistered release |
| Adversarial | Input only in the sealed promotion evaluation | No inputs, labels or detailed results; campaign outcome is recorded | Gate evaluation of preregistered finalists |
| Judge calibration | Only the inputs needed for a separate judge study | Not optimizer training data | Separate human labels and calibration analysis |

Programs inevitably receive holdout inputs while being evaluated. Enforce that
this happens only within the evaluator boundary with candidate mutation and
learning disabled, no persistent memory, no optimizer-readable traces, and no
holdout examples returned to the candidate author. The table is an access
requirement, not a claim that isolation already exists in this scaffold. If the
owner also authors candidates, inspecting detailed holdout results exposes that
holdout for future work; switching roles does not erase acquired knowledge.

Train data can improve candidate content. Development scores can guide selection,
but detailed dev labels or examples must not become candidate demonstrations or
reflection inputs. Adapters for DSPy/MLflow must preserve that boundary; passing
an unrestricted full dataset object into the optimizer is not sufficient.

A promotion campaign registers its dataset, gate, reference and candidate hash
before holdout access. One nominee is chosen from dev results. The Phase 9
MIPROv2/GEPA comparison may register both frozen contenders together, designate
its nominee before evaluating either, and evaluate them on the same holdout.
No replacement nominee or candidate revision is allowed after seeing holdout
outcomes. Results for the second contender are exploratory.

After a campaign reveals pass/fail or metrics to candidate authors, mark that
adversarial holdout exposed for future adaptive optimization. Before another
campaign can claim fresh holdout evidence, release new, disjoint hidden groups.
An evaluator-only infrastructure rerun may reuse the exact registered artifacts
under a new linked run ID if no results or examples were released and no candidate
changed. Record the reason; never erase the original failure.

The final test stays sealed until Phase 16. Once inspected, it becomes a historical
benchmark, not an untouched test for the next round of tuning. Publishing detailed
holdout reports exposes them and changes their permitted future use. Calibration
groups remain disjoint from optimization and holdout groups; a changed judge
requires new calibration evidence before use.

## Consequences

Store manifests, provenance, content hashes, review identities and exposure
records. Every change to data, labels, split assignment or policy binding creates
a new version. Validate duplicates, near-duplicate lineage and group separation
before admission. Missing review or uncertain source ownership quarantines a case.
The public documentation example is eligible only for train/illustration.

Use a separately permissioned evaluator/service identity for sealed artifacts.
Do not grant optimizer credentials read access to full holdout MLflow traces,
artifact storage or PostgreSQL rows. Logical split tags in a shared filesystem
or dataset object are insufficient. Evaluate only local task models under the
frozen profile; no cloud data upload is implied.

## Alternatives rejected

- Random row-level splitting: places related incident snapshots on both sides.
- Repeated adaptive promotion probes against one holdout: converts the gate into
  development feedback even if labels are hidden.
- Editing labels or split membership in place: destroys reproducible comparisons.
- Using public fixtures as hidden tests: mistakes familiar examples for independent
  evidence.

## Validation required in later phases

Reject duplicate IDs/digests, mismatched hashes, cross-split lineage, conflicting
labels, unreviewed cases and leaked fields in model inputs. Test that unauthorized
identities cannot read held-out data or traces, and that exposed holdouts cannot
support a new claim of untouched evaluation.

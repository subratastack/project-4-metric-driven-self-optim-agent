# ADR-001: Bounded offline optimization

- **Status:** Accepted for Phase 0; implementation pending
- **Date:** 2026-10-11
- **Contract:** optimization-boundary/v1

## Context

A better evaluation score is meaningful only when both programs obey the same
runtime and evaluation rules. A model that gains permission to restart a service
has changed the task, even if it resolves more test incidents. The first target
is therefore the incident investigator's next-action selector, not its whole
runtime or arbitrary source code.

## Decision

Use the [DecisionRequest and ActionDecision](../baseline-contract.md) contract.
The model selects a runtime-supplied action with fixed arguments, or proposes
finish, human escalation or abstention. Only the runtime executes anything.
Optimize offline, register immutable candidates, evaluate under unchanged
contracts, and require gated promotion and owner-approved activation.

The following is the **complete v1 optimizer write allowlist**:

| Field | Allowed values / bounds |
| --- | --- |
| `instruction_text` | UTF-8 NFC text, 1–8,000 characters; separate from immutable schema/security/renderer instructions |
| `demonstrations` | 0–4 examples drawn only from the registered train split; retain case IDs/hashes as lineage and pass only allowed model-visible input/output fields |
| `temperature` | Finite value in `[0.0, 0.7]`, if the fixed backend supports it; serialize as a decimal string in artifact metadata |
| `max_output_tokens` | One of `256`, `384`, `512`; may lower allocation, never raise the runtime ceiling |

DSPy-managed instructions/demonstrations are admissible only when representable
by these fields. Module topology, output schema, renderer, task model and
`top_p=1.0` stay fixed within a campaign. A supported parameter does not make
an invalid configuration eligible: all mandatory input, schema and instructions
must fit the 8,192-token ceiling without truncation, and runtime allowances may
be smaller. Unsupported values fail admission instead of being ignored.

**The optimizer may not change** tool names/descriptions/argument schemas or
arguments; authorization or approval rules; budgets/ceilings or accounting;
idempotency; database schemas; arbitrary Python/control flow; dependencies;
model/tokenizer identity; hidden data, split membership, labels, scorers,
metrics, thresholds or evidence; dataset/registry/deployment records; output
validation, retries, fallbacks, sampling seeds or holdout access rules.

Future numeric retrieval knobs such as top-K/context packing are not implicitly
allowed. Adding one needs a new boundary version with explicit range, ownership
and evaluation evidence. The optional tool-description experiment mentioned in
the curriculum similarly requires a separate boundary version. Separate
Predict/ChainOfThought profiles may be compared, but a candidate cannot switch
program topology inside its campaign.

The baseline is the exact human-authored prompt and single-call profile in the
baseline contract. Freeze an executable artifact only after its code, renderer,
model, tokenizer and environment are bound; no runnable baseline is claimed now.

## Consequences

The optimizer can improve selection while the runtime remains authoritative.
Action-argument synthesis is deliberately out of v1 scope, which may limit gains
but makes comparisons and policy checks inspectable. An instruction still may
induce an unsafe proposal; independent scorers and dispatch validation remain
mandatory. A shared process with unrestricted filesystem/DB access is not an
adequate isolation boundary for candidate generation and holdout evaluation.

## Alternatives rejected

- Whole-agent/code rewriting: changes execution semantics and invalidates the
  bounded comparison.
- Optimizer-owned policy or live prompt mutation: allows candidates to authorize
  themselves without reproducible gate evidence.
- Removing the runtime and using DSPy ReAct: changes the system under study.
- Generating arbitrary tool arguments: expands the first contract beyond action
  selection and requires a separate argument-validation/evaluation design.

## Validation required in later phases

Reject unknown candidate fields, out-of-range knobs, modified tool arguments,
changed policies/models and unauthorized artifact writes. Demonstrate failure
accounting, live reauthorization, interrupted-run rejection, atomic activation
and rollback before integration. The [architecture](../../ARCHITECTURE.md)
defines ownership; the [metrics](../metrics.md) define gate evidence.

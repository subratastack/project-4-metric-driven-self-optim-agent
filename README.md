# Metric-Driven Self-Optimizing Agent

A local experiment project for improving an incident investigator's next-action
selection while keeping tool permissions, execution and evaluation outside the
candidate's control.

**Status: Phase 1 implementation and Qwen3 local verification are available;
independent dataset review remains pending.** The project includes a frozen baseline implementation,
strict dataset validation, 100 synthetic draft cases, deterministic correctness
and safety scorers, and a sequential evaluation harness. No optimizer, judge,
tracking integration or production runtime adapter is implemented.

The approved core and development dependencies remain in this project's own
`.venv`. This phase adds no dependencies, downloads no models, starts no services
and executes no incident tools. The [Phase 1 review](docs/phase-1-review.md)
records implementation status. The [Qwen3 verification](docs/qwen3-local-verification.md)
records five real local calls: transport/token counts passed, but every response
failed the output union because it populated a hypothesis ID for a tool call.

Based on the [Notion guided build](https://app.notion.com/p/3e8456c5513581f89164d6f511de8f70)
and the Python conventions of
[`project-3-long-term-agent-memory`](../project-3-long-term-agent-memory/).

## Try the implemented checks

From this project directory, using the existing environment:

```bash
.venv/bin/python -m scripts.build_dataset --check
.venv/bin/python -m scripts.validate_dataset --allow-draft
.venv/bin/python -m scripts.run_baseline --verify
.venv/bin/python -m pytest -q
.venv/bin/ruff check apps scripts tests
.venv/bin/ruff format --check apps scripts tests
.venv/bin/mypy apps scripts tests
```

These commands need no model server. Tests use clearly identified backend test
doubles; passing tests is not a measured baseline accuracy result.

The corpus contains **40 train / 20 dev / 20 test / 20 adversarial** cases from
50 incident lineages. Each incident contributes two snapshots to the same split.
The [case index](datasets/REVIEW.md) and [source scenarios](datasets/source/scenarios.json)
make labels reviewable. All labels await independent review, and all four splits
are exposed curriculum material. They cannot support an untouched-holdout claim.
The loader rejects the draft by default; `--allow-draft` is an explicit opt-in to
structural validation or exploratory evaluation, not release approval.

## Baseline execution boundary

The baseline uses the exact Phase 0 instruction, zero demonstrations, one model
call, temperature zero, the fixed five-seed schedule, no retries and no JSON
repair. It proposes a typed next action without executing it. Scorers separately
record invalid output, unsafe proposals, correctness, citation support and
repetition. Failed attempts remain in the scheduled denominator.

The [freeze manifest](apps/decision_program/baseline.freeze.json) binds the prompt,
envelope, schema, implementation, tool policy and dependency lockfile. It retains its original implementation-only identity. The separate
[execution binding](apps/decision_program/model_bindings/qwen3-14b-ollama-0.20.0.json)
binds the existing `qwen3:14b` model and the included Ollama adapter. See the
[local verification record](docs/qwen3-local-verification.md) for measured failures,
tokenizer conformance and opt-in commands. No full benchmark has been run.

## Project layout

```text
apps/decision_program/    Strict contracts, tool catalogue, frozen prompt and baseline
apps/evaluation/          Dataset loader, sequential runner and deterministic metrics
apps/optimization/        Reserved for later phases; placeholders only
datasets/source/          Fifty authored incident scenarios
datasets/cases/           One canonical JSONL file per split; 100 draft records
datasets/manifests/       Manifest, record/file hashes and external manifest digest
docs/                     Architecture decisions, contracts and phase review records
scripts/                  Dataset builder/validator and baseline entry point
tests/                    Contract, corpus, scorer and runner tests
```

DSPy modules, MLflow, Inspect AI, statistical comparisons, control-plane storage,
telemetry and optional experiments remain deferred. Project 1 is absent, so no
integration with its runtime is claimed.

## Approved environment

Python 3.12 is the development target. This project uses its isolated environment;
it does not import or modify Project 3. Direct versions are pinned in
`pyproject.toml`, with transitive versions in `uv.lock`. To reproduce the already
approved dependencies from this directory:

```bash
uv sync --locked --group dev --no-install-project --python 3.12
```

Run modules from the project directory; an editable install is unnecessary.
Optional packages remain excluded. GEPA is present only because DSPy requires it;
no optimizer is invoked. See the [dependency record](docs/dependencies.md) and
[license inventory](docs/dependency-licenses.md).

The [provider strategy](docs/model-providers.md) selects local Ollama or OpenRouter
through `.env`. OpenRouter requires one explicit `OPENROUTER_MODEL` and an API key
in that file; there is no model override or fallback. The existing frozen baseline
and evaluation runner retain their local-only contract. No live OpenRouter call
has been made. PostgreSQL Compose settings remain future templates; neither model
strategy requires databases or MLflow.

## Design and progress

- [Architecture](ARCHITECTURE.md)
- [ADR-001: optimization boundary](docs/adr/001-optimization-boundary.md)
- [ADR-002: metric hierarchy](docs/adr/002-metric-hierarchy.md)
- [ADR-003: splits and leakage](docs/adr/003-dataset-splits-and-leakage.md)
- [Decision and frozen baseline contract](docs/baseline-contract.md)
- [Dataset schema](docs/dataset-schema.md) and [synthetic tool catalogue](docs/tool-catalog.md)
- [Metric definitions](docs/metrics.md)
- [Phase 0 design record](docs/phase-0-review.md) and [Phase 1 implementation review](docs/phase-1-review.md)
- [Guided roadmap](docs/roadmap.md)

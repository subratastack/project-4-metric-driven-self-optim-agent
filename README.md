# Metric-Driven Self-Optimizing Agent

A planned local optimization platform for improving one bounded agent decision
component through reproducible experiments and controlled promotion.

**Status: Phase 0 documentation finalized; implementation is scaffold only.**
Python modules contain documentation placeholders.
No baseline, dataset loader, scorer, optimizer, database model, or integration
has been implemented. The approved core and development dependencies are
installed in this project's isolated `.venv`.

Based on the [Project 4 guided build in Notion](https://app.notion.com/p/3e8456c5513581f89164d6f511de8f70)
and the Python project conventions in
[`project-3-long-term-agent-memory`](../project-3-long-term-agent-memory/).

## Intended behavior

An incident investigator chooses a next action from the available evidence,
tools, and remaining budget. This project will compare a frozen baseline with
candidate instructions, demonstrations, and bounded configuration changes.
A candidate is a versioned proposal, not an active runtime change.

For example, in an illustrative checkout-api incident, a candidate might choose
a useful diagnostic tool sooner than the baseline. It must still produce a
valid decision and obey the runtime's tool policy. A better average score will
not compensate for a forbidden action. These are design requirements, not
implemented or measured behavior.

## Project layout

```text
project-4-metric-driven-self-optim-agent/
├── README.md, ARCHITECTURE.md, pyproject.toml
├── .env.example, .python-version, docker-compose.yml
├── docs/
│   ├── adr/                     # Three accepted Phase 0 design decisions
│   ├── baseline-contract.md     # Decision interface, frozen prompt and failures
│   ├── dataset-schema.md        # Case/manifest schema and split validation
│   ├── metrics.md               # Metrics, uncertainty and promotion profile
│   ├── phase-0-review.md        # Design handoff and execution prerequisites
│   ├── dependencies.md          # Installed core/development library record
│   └── roadmap.md               # Guided phases and review gates
├── datasets/{manifests,fixtures}/
├── apps/
│   ├── decision_program/        # Signature, baseline, module, adapter, versions
│   ├── evaluation/              # Datasets, repeated runs, statistics
│   │   ├── metrics/             # Correctness, policy, efficiency, usage
│   │   └── judges/              # Optional calibrated local judge
│   ├── optimization/            # Candidate generation, registry, promotion
│   ├── mlflow_integration/      # Tracking, datasets, scorers, prompt versions
│   ├── inspect_eval/            # Independent evaluation harness
│   ├── telemetry/               # Traces, metrics, shared attributes
│   └── control_plane/           # Future persistence and service boundary
├── experiments/{textgrad_compare,optuna_multiobjective,botorch_frontier}/
├── scripts/                     # Future entry points; currently docstrings only
└── tests/{unit,integration,evaluation,optimization,adversarial,regression}/
```

## Development environment

Python 3.12 is the development target, matching Project 3. The environment uses
the existing CPython 3.12.3 interpreter and does not share Project 3's packages.
Hatchling, pytest, Ruff, mypy, and coverage configuration follow its conventions.
The core and development libraries were approved on 2026-10-11. Direct versions
are pinned in `pyproject.toml`; `uv.lock` records exact transitive versions.

From the workspace root, activate the installed environment:

```bash
cd project-4-metric-driven-self-optim-agent
source .venv/bin/activate
```

To reproduce the approved dependency environment from the project directory:

```bash
uv sync --locked --group dev --no-install-project --python 3.12
```

This installs dependencies only. The scaffold is used directly from the project
directory, and the project itself is not installed as an editable distribution.
Optional experiment packages remain excluded. DSPy requires GEPA transitively,
so GEPA is present without any optimizer being run. See the
[dependency record](docs/dependencies.md) and
[resolved license inventory](docs/dependency-licenses.md).

Development checks can run inside the activated environment:

```bash
ruff check apps scripts
ruff format --check apps scripts
mypy apps scripts
pytest --collect-only -q
```

There are no feature tests yet. Pytest's collection-only command therefore
reports no tests and exits with code 5; this is not a passing behavioral suite.

`.env.example` documents future local settings; no application reads them yet.
The Compose file is a PostgreSQL infrastructure template behind the explicit
`infrastructure` profile. It uses localhost port 5433 to distinguish it from
Project 3's default 5432. No images have been pulled or services started.
MLflow and model-serving setup remain deferred.

## Phase 0 design documents

- [Final architecture](ARCHITECTURE.md)
- [Optimization boundary](docs/adr/001-optimization-boundary.md)
- [Metric hierarchy](docs/adr/002-metric-hierarchy.md)
- [Dataset splits and leakage](docs/adr/003-dataset-splits-and-leakage.md)
- [Dataset schema and illustrative case](docs/dataset-schema.md)
- [Metric definitions and comparison gates](docs/metrics.md)
- [Frozen baseline and decision contract](docs/baseline-contract.md)
- [Phase 0 review record](docs/phase-0-review.md)
- [Guided roadmap](docs/roadmap.md)

Phase 0 defines the v1 contract; it does not freeze an executable baseline or
release a dataset. Phase 1 must bind the selected local model and tokenizer,
implement the renderer and validators, and create reviewed cases before a run.
Project 1 is absent from this workspace, so its future adapter must demonstrate
conformance to this documented boundary before any integration claim. Further
implementation starts only when requested.

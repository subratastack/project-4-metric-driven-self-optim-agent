# Dependency and license record

**Core and development dependencies approved and installed on 2026-10-11.**

The tables below identify the approved direct versions and their license
sources. `uv.lock` records the complete resolved dependency graph. The isolated
CPython 3.12.3 environment contains 176 third-party packages, including the 19
approved core/development libraries and their required dependencies. The
[resolved license inventory](dependency-licenses.md) records all 180 third-party
versions in the universal lockfile; four are for other platforms.

Before installation, package-maintainer metadata and missing upstream license
files were checked. SciPy's bundled GCC runtime exception and libquadmath
licenses are documented in that inventory. Installed distributions retain
their notices. The environment passed `uv pip check` and matches the lockfile.

## Installed core Python libraries

| Library / source | Reviewed version | License | Planned purpose |
| --- | --- | --- | --- |
| [dspy](https://pypi.org/project/dspy/3.4.0/) | 3.4.0 | MIT | Typed decision programs, MIPROv2 and GEPA interfaces |
| [mlflow](https://pypi.org/project/mlflow/3.17.0/) | 3.17.0 | Apache-2.0 | Experiment tracking, GenAI evaluation and version lineage |
| [inspect-ai](https://pypi.org/project/inspect-ai/0.3.278/) | 0.3.278 | MIT | Independent evaluation harness |
| [numpy](https://pypi.org/project/numpy/2.5.4/) | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | Array operations and repeated-run analysis |
| [scipy](https://pypi.org/project/scipy/1.18.1/) | 1.18.1 | BSD-3-Clause (main project; binary distribution notices also apply) | Statistical analysis and confidence intervals |
| [pydantic](https://pypi.org/project/pydantic/2.14.0/) | 2.14.0 | MIT | Typed input/output and control-plane contracts |
| [pydantic-settings](https://pypi.org/project/pydantic-settings/2.15.0/) | 2.15.0 | MIT | Environment-based settings, following Project 3 |
| [sqlalchemy](https://pypi.org/project/sqlalchemy/2.1.4/) | 2.1.4 | MIT | PostgreSQL persistence, following Project 3 |
| [alembic](https://pypi.org/project/alembic/1.20.0/) | 1.20.0 | MIT | Future schema migrations, following Project 3 |
| [psycopg](https://pypi.org/project/psycopg/3.3.6/) | 3.3.6 | LGPL-3.0-only | PostgreSQL driver; plain package without binary/pool extras |
| [opentelemetry-api](https://pypi.org/project/opentelemetry-api/1.45.1/) | 1.45.1 | Apache-2.0 | Tracing and metric interfaces |
| [opentelemetry-sdk](https://pypi.org/project/opentelemetry-sdk/1.45.1/) | 1.45.1 | Apache-2.0 | Local telemetry implementation |
| [opentelemetry-exporter-otlp-proto-http](https://pypi.org/project/opentelemetry-exporter-otlp-proto-http/1.45.1/) | 1.45.1 | Apache-2.0 | OTLP HTTP trace/metric export |

## Installed build and development tools

| Library / source | Reviewed version | License | Planned purpose |
| --- | --- | --- | --- |
| [hatchling](https://pypi.org/project/hatchling/1.32.4/) | 1.32.4 | MIT | Declared build backend and development build tooling |
| [pytest](https://pypi.org/project/pytest/9.1.1/) | 9.1.1 | MIT | Future test execution |
| [pytest-cov](https://pypi.org/project/pytest-cov/7.1.0/) | 7.1.0 | MIT | Future coverage reporting |
| [hypothesis](https://pypi.org/project/hypothesis/6.169.0/) | 6.169.0 | MPL-2.0 | Future property-based tests for invariants |
| [ruff](https://pypi.org/project/ruff/0.17.0/) | 0.17.0 | MIT | Linting and formatting |
| [mypy](https://pypi.org/project/mypy/2.4.0/) | 2.4.0 | MIT | Static type checking |

## Later framework support and optional experiments

| Library / source | Reviewed version | License | Planned purpose |
| --- | --- | --- | --- |
| [optuna](https://pypi.org/project/optuna/5.0.0/) | 5.0.0 | MIT | Not installed; optional MIPROv2/Pareto support for a later phase |
| [gepa](https://pypi.org/project/gepa/0.1.4/) | 0.1.4 | MIT | Installed because DSPy 3.4.0 requires gepa[dspy]==0.1.4 |
| [openinference-instrumentation-dspy](https://pypi.org/project/openinference-instrumentation-dspy/0.1.48/) | 0.1.48 | Apache-2.0 | Optional DSPy trace instrumentation |
| [arize-phoenix](https://pypi.org/project/arize-phoenix/20.20.0/) | 20.20.0 | Elastic-2.0 (ELv2) | Optional local trace viewer |
| [textgrad](https://pypi.org/project/textgrad/0.1.8/) | 0.1.8 | MIT | Later textual-gradient comparison |
| [ax-platform](https://pypi.org/project/ax-platform/1.3.1/) | 1.3.1 | MIT | Optional frontier search |
| [botorch](https://pypi.org/project/botorch/0.18.1/) | 0.18.1 | MIT | Optional frontier search |

Optional experiment packages were skipped. GEPA is the required DSPy support
dependency, not an added experiment. Optuna, Phoenix, OpenInference DSPy
instrumentation, TextGrad, Ax, BoTorch, and vLLM are absent. No optimizer or
experiment has been implemented or run.

## External services and model runtimes

| Component / source | License | Status |
| --- | --- | --- |
| [PostgreSQL](https://www.postgresql.org/about/licence/) | PostgreSQL License | Version 17 Compose template only; no image pull or startup |
| [Ollama](https://github.com/ollama/ollama/blob/main/LICENSE) | MIT | Proposed local model server; no install or model download |
| [vLLM](https://github.com/vllm-project/vllm/blob/main/LICENSE) | Apache-2.0 | Alternative model server; deferred |

MLflow server licensing is covered by the MLflow entry above. PostgreSQL
client library libpq uses the PostgreSQL License. Plain Psycopg uses the
existing system libpq; no system package installation was needed or performed.
Container images and model runtimes include additional components. Model
weights have separate licenses and no model has been selected.

## License details relevant to the selection

- Psycopg is LGPL-3.0-only; it is not covered by the MIT license of SQLAlchemy.
- Hypothesis is MPL-2.0; it is installed as a development dependency.
- Phoenix uses [Elastic License 2.0](https://github.com/Arize-ai/phoenix/blob/main/LICENSE).
  Keep this separate from the Apache-2.0 OpenInference instrumentation.
- NumPy publishes a combined license expression for its included components.
  SciPy's [main license](https://github.com/scipy/scipy/blob/main/LICENSE.txt)
  is BSD-3-Clause; actual wheels may include additional library notices.
  Review selected wheel licenses as part of the resolved inventory.

## Reproducing the environment

From the project directory, use the existing Python 3.12 interpreter:

```bash
uv sync --locked --group dev --no-install-project --python 3.12
uv pip check --python .venv/bin/python
```

The project itself is not installed as an editable distribution; its placeholder
modules can be imported from the project directory. New optional dependencies
still need review and approval. No feature implementation, optimizer run, model
download, database creation, or service startup was performed during setup.

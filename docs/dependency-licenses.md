# Resolved dependency license inventory

Resolution date: 2026-10-11. Target: CPython 3.12.3 on Linux x86_64.
The core/development installation plan contains 176 third-party packages.
The universal lockfile also includes four packages for other supported platforms.
The project itself is excluded from this third-party license inventory.

Sources are version-specific maintainer metadata from PyPI; source-license links
fill missing metadata. This is a package-level inventory, not a legal opinion
or a file-by-file audit. Installed distributions retain their bundled notices.

DSPy 3.4.0 requires `gepa[dspy]==0.1.4`; GEPA is therefore included as a
mandatory transitive dependency. Optuna, Phoenix, OpenInference DSPy
instrumentation, TextGrad, Ax, BoTorch, and vLLM are absent from the lockfile.

SciPy's published license metadata also lists OpenBLAS (BSD-3-Clause), LAPACK
(BSD-3-Clause-Open-MPI), GCC runtime (GPL-3.0-or-later WITH GCC-exception-3.1),
and libquadmath (LGPL-2.1-or-later). Preserve these bundled notices.
NumPy's combined SPDX expression is retained below; wheel notices are additional
evidence and are retained in the installed distribution.

| Package | Locked version | Linux 3.12 plan | Published license / source |
| --- | --- | --- | --- |
| [agent-client-protocol](https://pypi.org/project/agent-client-protocol/0.12.1/) | 0.12.1 | Yes | [Apache-2.0](https://github.com/agentclientprotocol/python-sdk/blob/main/LICENSE) |
| [aiobotocore](https://pypi.org/project/aiobotocore/3.9.2/) | 3.9.2 | Yes | [Apache-2.0](https://pypi.org/project/aiobotocore/3.9.2/) |
| [aiohappyeyeballs](https://pypi.org/project/aiohappyeyeballs/2.7.1/) | 2.7.1 | Yes | [PSF license](https://pypi.org/project/aiohappyeyeballs/2.7.1/) |
| [aiohttp](https://pypi.org/project/aiohttp/3.14.5/) | 3.14.5 | Yes | [Apache-2.0 AND MIT](https://pypi.org/project/aiohttp/3.14.5/) |
| [aioitertools](https://pypi.org/project/aioitertools/0.13.0/) | 0.13.0 | Yes | [MIT](https://pypi.org/project/aioitertools/0.13.0/) |
| [aiosignal](https://pypi.org/project/aiosignal/1.4.0/) | 1.4.0 | Yes | [Apache-2.0](https://pypi.org/project/aiosignal/1.4.0/) |
| [alembic](https://pypi.org/project/alembic/1.20.0/) | 1.20.0 | Yes | [MIT](https://pypi.org/project/alembic/1.20.0/) |
| [annotated-doc](https://pypi.org/project/annotated-doc/0.0.5/) | 0.0.5 | Yes | [MIT](https://pypi.org/project/annotated-doc/0.0.5/) |
| [annotated-types](https://pypi.org/project/annotated-types/0.8.0/) | 0.8.0 | Yes | [MIT](https://pypi.org/project/annotated-types/0.8.0/) |
| [anyio](https://pypi.org/project/anyio/4.15.1/) | 4.15.1 | Yes | [MIT](https://pypi.org/project/anyio/4.15.1/) |
| [ast-serialize](https://pypi.org/project/ast-serialize/0.12.1/) | 0.12.1 | Yes | [MIT](https://pypi.org/project/ast-serialize/0.12.1/) |
| [attrs](https://pypi.org/project/attrs/26.1.0/) | 26.1.0 | Yes | [MIT](https://pypi.org/project/attrs/26.1.0/) |
| [beautifulsoup4](https://pypi.org/project/beautifulsoup4/4.15.0/) | 4.15.0 | Yes | [MIT](https://pypi.org/project/beautifulsoup4/4.15.0/) |
| [blinker](https://pypi.org/project/blinker/1.9.0/) | 1.9.0 | Yes | [MIT](https://pypi.org/project/blinker/1.9.0/) |
| [boto3](https://pypi.org/project/boto3/1.43.106/) | 1.43.106 | Yes | [Apache-2.0](https://pypi.org/project/boto3/1.43.106/) |
| [botocore](https://pypi.org/project/botocore/1.43.106/) | 1.43.106 | Yes | [Apache-2.0](https://pypi.org/project/botocore/1.43.106/) |
| [cachetools](https://pypi.org/project/cachetools/7.2.1/) | 7.2.1 | Yes | [MIT](https://pypi.org/project/cachetools/7.2.1/) |
| [certifi](https://pypi.org/project/certifi/2026.7.22/) | 2026.7.22 | Yes | [MPL-2.0](https://pypi.org/project/certifi/2026.7.22/) |
| [cffi](https://pypi.org/project/cffi/2.1.1/) | 2.1.1 | Yes | [MIT-0](https://pypi.org/project/cffi/2.1.1/) |
| [charset-normalizer](https://pypi.org/project/charset-normalizer/3.5.2/) | 3.5.2 | Yes | [MIT](https://pypi.org/project/charset-normalizer/3.5.2/) |
| [click](https://pypi.org/project/click/8.5.0/) | 8.5.0 | Yes | [BSD-3-Clause](https://pypi.org/project/click/8.5.0/) |
| [cloudpickle](https://pypi.org/project/cloudpickle/3.1.2/) | 3.1.2 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/cloudpickle/3.1.2/) |
| [colorama](https://pypi.org/project/colorama/0.4.6/) | 0.4.6 | Other platform | [BSD (maintainer classification; see package license)](https://pypi.org/project/colorama/0.4.6/) |
| [contourpy](https://pypi.org/project/contourpy/1.4.0/) | 1.4.0 | Yes | [BSD-3-Clause](https://pypi.org/project/contourpy/1.4.0/) |
| [coverage](https://pypi.org/project/coverage/7.16.2/) | 7.16.2 | Yes | [Apache-2.0](https://pypi.org/project/coverage/7.16.2/) |
| [cryptography](https://pypi.org/project/cryptography/50.0.2/) | 50.0.2 | Yes | [Apache-2.0 OR BSD-3-Clause](https://pypi.org/project/cryptography/50.0.2/) |
| [cycler](https://pypi.org/project/cycler/0.12.1/) | 0.12.1 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/cycler/0.12.1/) |
| [databricks-sdk](https://pypi.org/project/databricks-sdk/0.151.0/) | 0.151.0 | Yes | [Apache-2.0](https://pypi.org/project/databricks-sdk/0.151.0/) |
| [debugpy](https://pypi.org/project/debugpy/1.8.22/) | 1.8.22 | Yes | [MIT](https://pypi.org/project/debugpy/1.8.22/) |
| [diskcache](https://pypi.org/project/diskcache/5.6.3/) | 5.6.3 | Yes | [Apache-2.0](https://pypi.org/project/diskcache/5.6.3/) |
| [distro](https://pypi.org/project/distro/1.9.0/) | 1.9.0 | Yes | [Apache-2.0](https://pypi.org/project/distro/1.9.0/) |
| [docker](https://pypi.org/project/docker/7.2.0/) | 7.2.0 | Yes | [Apache-2.0](https://pypi.org/project/docker/7.2.0/) |
| [docstring-parser](https://pypi.org/project/docstring-parser/0.18.0/) | 0.18.0 | Yes | [MIT](https://pypi.org/project/docstring-parser/0.18.0/) |
| [dspy](https://pypi.org/project/dspy/3.4.0/) | 3.4.0 | Yes | [MIT License](https://pypi.org/project/dspy/3.4.0/) |
| [fastapi](https://pypi.org/project/fastapi/0.143.0/) | 0.143.0 | Yes | [MIT](https://pypi.org/project/fastapi/0.143.0/) |
| [fastuuid](https://pypi.org/project/fastuuid/0.14.0/) | 0.14.0 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/fastuuid/0.14.0/) |
| [filelock](https://pypi.org/project/filelock/3.32.7/) | 3.32.7 | Yes | [MIT](https://pypi.org/project/filelock/3.32.7/) |
| [flask](https://pypi.org/project/flask/3.1.3/) | 3.1.3 | Yes | [BSD-3-Clause](https://pypi.org/project/flask/3.1.3/) |
| [flask-cors](https://pypi.org/project/flask-cors/6.0.5/) | 6.0.5 | Yes | [MIT](https://pypi.org/project/flask-cors/6.0.5/) |
| [fonttools](https://pypi.org/project/fonttools/4.66.1/) | 4.66.1 | Yes | [MIT](https://pypi.org/project/fonttools/4.66.1/) |
| [frozenlist](https://pypi.org/project/frozenlist/1.8.0/) | 1.8.0 | Yes | [Apache-2.0](https://pypi.org/project/frozenlist/1.8.0/) |
| [fsspec](https://pypi.org/project/fsspec/2026.6.0/) | 2026.6.0 | Yes | [BSD-3-Clause](https://pypi.org/project/fsspec/2026.6.0/) |
| [gepa](https://pypi.org/project/gepa/0.1.4/) | 0.1.4 | Yes | [MIT](https://pypi.org/project/gepa/0.1.4/) |
| [gitdb](https://pypi.org/project/gitdb/4.0.12/) | 4.0.12 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/gitdb/4.0.12/) |
| [gitpython](https://pypi.org/project/gitpython/3.2.0/) | 3.2.0 | Yes | [BSD-3-Clause](https://pypi.org/project/gitpython/3.2.0/) |
| [google-auth](https://pypi.org/project/google-auth/2.61.0/) | 2.61.0 | Yes | [Apache-2.0](https://pypi.org/project/google-auth/2.61.0/) |
| [googleapis-common-protos](https://pypi.org/project/googleapis-common-protos/1.75.5/) | 1.75.5 | Yes | [Apache-2.0](https://pypi.org/project/googleapis-common-protos/1.75.5/) |
| [graphene](https://pypi.org/project/graphene/3.4.3/) | 3.4.3 | Yes | [MIT](https://pypi.org/project/graphene/3.4.3/) |
| [graphql-core](https://pypi.org/project/graphql-core/3.2.13/) | 3.2.13 | Yes | [MIT](https://pypi.org/project/graphql-core/3.2.13/) |
| [graphql-relay](https://pypi.org/project/graphql-relay/3.2.0/) | 3.2.0 | Yes | [MIT](https://pypi.org/project/graphql-relay/3.2.0/) |
| [gunicorn](https://pypi.org/project/gunicorn/26.2.0/) | 26.2.0 | Yes | [MIT](https://pypi.org/project/gunicorn/26.2.0/) |
| [h11](https://pypi.org/project/h11/0.16.0/) | 0.16.0 | Yes | [MIT](https://pypi.org/project/h11/0.16.0/) |
| [h2](https://pypi.org/project/h2/4.4.1/) | 4.4.1 | Yes | [MIT](https://pypi.org/project/h2/4.4.1/) |
| [hatchling](https://pypi.org/project/hatchling/1.32.4/) | 1.32.4 | Yes | [MIT](https://pypi.org/project/hatchling/1.32.4/) |
| [hf-xet](https://pypi.org/project/hf-xet/1.7.0/) | 1.7.0 | Yes | [Apache-2.0](https://pypi.org/project/hf-xet/1.7.0/) |
| [hpack](https://pypi.org/project/hpack/4.2.0/) | 4.2.0 | Yes | [MIT](https://pypi.org/project/hpack/4.2.0/) |
| [httpcore](https://pypi.org/project/httpcore/1.0.9/) | 1.0.9 | Yes | [BSD-3-Clause](https://pypi.org/project/httpcore/1.0.9/) |
| [httpx](https://pypi.org/project/httpx/0.28.1/) | 0.28.1 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/httpx/0.28.1/) |
| [huey](https://pypi.org/project/huey/3.4.0/) | 3.4.0 | Yes | [MIT](https://github.com/coleifer/huey/blob/master/LICENSE) |
| [huggingface-hub](https://pypi.org/project/huggingface-hub/1.33.0/) | 1.33.0 | Yes | [Apache-2.0](https://pypi.org/project/huggingface-hub/1.33.0/) |
| [hyperframe](https://pypi.org/project/hyperframe/6.1.0/) | 6.1.0 | Yes | [MIT](https://pypi.org/project/hyperframe/6.1.0/) |
| [hypothesis](https://pypi.org/project/hypothesis/6.169.0/) | 6.169.0 | Yes | [MPL-2.0](https://pypi.org/project/hypothesis/6.169.0/) |
| [idna](https://pypi.org/project/idna/3.20/) | 3.20 | Yes | [BSD-3-Clause](https://pypi.org/project/idna/3.20/) |
| [ijson](https://pypi.org/project/ijson/3.5.1/) | 3.5.1 | Yes | [BSD-3-Clause AND ISC](https://pypi.org/project/ijson/3.5.1/) |
| [importlib-metadata](https://pypi.org/project/importlib-metadata/8.9.0/) | 8.9.0 | Yes | [Apache-2.0](https://pypi.org/project/importlib-metadata/8.9.0/) |
| [iniconfig](https://pypi.org/project/iniconfig/2.3.1/) | 2.3.1 | Yes | [MIT](https://pypi.org/project/iniconfig/2.3.1/) |
| [inspect-ai](https://pypi.org/project/inspect-ai/0.3.278/) | 0.3.278 | Yes | [MIT](https://pypi.org/project/inspect-ai/0.3.278/) |
| [itsdangerous](https://pypi.org/project/itsdangerous/2.2.0/) | 2.2.0 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/itsdangerous/2.2.0/) |
| [jinja2](https://pypi.org/project/jinja2/3.1.6/) | 3.1.6 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/jinja2/3.1.6/) |
| [jiter](https://pypi.org/project/jiter/0.17.0/) | 0.17.0 | Yes | [MIT](https://pypi.org/project/jiter/0.17.0/) |
| [jmespath](https://pypi.org/project/jmespath/1.1.0/) | 1.1.0 | Yes | [MIT](https://pypi.org/project/jmespath/1.1.0/) |
| [joblib](https://pypi.org/project/joblib/1.6.0/) | 1.6.0 | Yes | [BSD-3-Clause](https://pypi.org/project/joblib/1.6.0/) |
| [json-repair](https://pypi.org/project/json-repair/0.64.0/) | 0.64.0 | Yes | [MIT](https://pypi.org/project/json-repair/0.64.0/) |
| [jsonlines](https://pypi.org/project/jsonlines/4.0.0/) | 4.0.0 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/jsonlines/4.0.0/) |
| [jsonpatch](https://pypi.org/project/jsonpatch/1.35/) | 1.35 | Yes | [BSD-3-Clause](https://pypi.org/project/jsonpatch/1.35/) |
| [jsonpath-ng](https://pypi.org/project/jsonpath-ng/1.10.0/) | 1.10.0 | Yes | [Apache-2.0](https://pypi.org/project/jsonpath-ng/1.10.0/) |
| [jsonpointer](https://pypi.org/project/jsonpointer/3.2.1/) | 3.2.1 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/jsonpointer/3.2.1/) |
| [jsonref](https://pypi.org/project/jsonref/1.1.0/) | 1.1.0 | Yes | [MIT](https://pypi.org/project/jsonref/1.1.0/) |
| [jsonschema](https://pypi.org/project/jsonschema/4.26.0/) | 4.26.0 | Yes | [MIT](https://pypi.org/project/jsonschema/4.26.0/) |
| [jsonschema-specifications](https://pypi.org/project/jsonschema-specifications/2025.9.1/) | 2025.9.1 | Yes | [MIT](https://pypi.org/project/jsonschema-specifications/2025.9.1/) |
| [kiwisolver](https://pypi.org/project/kiwisolver/1.5.1/) | 1.5.1 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/kiwisolver/1.5.1/) |
| [librt](https://pypi.org/project/librt/0.16.0/) | 0.16.0 | Yes | [MIT](https://pypi.org/project/librt/0.16.0/) |
| [linkify-it-py](https://pypi.org/project/linkify-it-py/2.2.0/) | 2.2.0 | Yes | [MIT](https://pypi.org/project/linkify-it-py/2.2.0/) |
| [litellm](https://pypi.org/project/litellm/1.105.0/) | 1.105.0 | Yes | [MIT](https://pypi.org/project/litellm/1.105.0/) |
| [mako](https://pypi.org/project/mako/1.4.3/) | 1.4.3 | Yes | [MIT](https://pypi.org/project/mako/1.4.3/) |
| [markdown-it-py](https://pypi.org/project/markdown-it-py/4.2.0/) | 4.2.0 | Yes | [MIT](https://pypi.org/project/markdown-it-py/4.2.0/) |
| [markupsafe](https://pypi.org/project/markupsafe/3.0.4/) | 3.0.4 | Yes | [BSD-3-Clause](https://pypi.org/project/markupsafe/3.0.4/) |
| [matplotlib](https://pypi.org/project/matplotlib/3.11.2/) | 3.11.2 | Yes | [PSF license](https://pypi.org/project/matplotlib/3.11.2/) |
| [mdit-py-plugins](https://pypi.org/project/mdit-py-plugins/0.6.1/) | 0.6.1 | Yes | [MIT](https://pypi.org/project/mdit-py-plugins/0.6.1/) |
| [mdurl](https://pypi.org/project/mdurl/0.1.2/) | 0.1.2 | Yes | [MIT](https://pypi.org/project/mdurl/0.1.2/) |
| [mlflow](https://pypi.org/project/mlflow/3.17.0/) | 3.17.0 | Yes | [Apache-2.0](https://pypi.org/project/mlflow/3.17.0/) |
| [mlflow-skinny](https://pypi.org/project/mlflow-skinny/3.17.0/) | 3.17.0 | Yes | [Apache-2.0](https://pypi.org/project/mlflow-skinny/3.17.0/) |
| [mlflow-tracing](https://pypi.org/project/mlflow-tracing/3.17.0/) | 3.17.0 | Yes | [Apache-2.0](https://pypi.org/project/mlflow-tracing/3.17.0/) |
| [mmh3](https://pypi.org/project/mmh3/5.3.1/) | 5.3.1 | Yes | [MIT](https://pypi.org/project/mmh3/5.3.1/) |
| [multidict](https://pypi.org/project/multidict/6.9.1/) | 6.9.1 | Yes | [Apache License 2.0](https://pypi.org/project/multidict/6.9.1/) |
| [mypy](https://pypi.org/project/mypy/2.4.0/) | 2.4.0 | Yes | [MIT](https://pypi.org/project/mypy/2.4.0/) |
| [mypy-extensions](https://pypi.org/project/mypy-extensions/1.1.0/) | 1.1.0 | Yes | [MIT](https://github.com/python/mypy_extensions/blob/master/LICENSE) |
| [narwhals](https://pypi.org/project/narwhals/2.27.1/) | 2.27.1 | Yes | [MIT](https://pypi.org/project/narwhals/2.27.1/) |
| [nest-asyncio2](https://pypi.org/project/nest-asyncio2/1.7.4/) | 1.7.4 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/nest-asyncio2/1.7.4/) |
| [numpy](https://pypi.org/project/numpy/2.5.4/) | 2.5.4 | Yes | [BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0](https://pypi.org/project/numpy/2.5.4/) |
| [openai](https://pypi.org/project/openai/2.54.0/) | 2.54.0 | Yes | [Apache-2.0](https://pypi.org/project/openai/2.54.0/) |
| [opentelemetry-api](https://pypi.org/project/opentelemetry-api/1.45.1/) | 1.45.1 | Yes | [Apache-2.0](https://pypi.org/project/opentelemetry-api/1.45.1/) |
| [opentelemetry-exporter-http-transport](https://pypi.org/project/opentelemetry-exporter-http-transport/0.66b1/) | 0.66b1 | Yes | [Apache-2.0](https://pypi.org/project/opentelemetry-exporter-http-transport/0.66b1/) |
| [opentelemetry-exporter-otlp-common](https://pypi.org/project/opentelemetry-exporter-otlp-common/0.66b1/) | 0.66b1 | Yes | [Apache-2.0](https://pypi.org/project/opentelemetry-exporter-otlp-common/0.66b1/) |
| [opentelemetry-exporter-otlp-proto-common](https://pypi.org/project/opentelemetry-exporter-otlp-proto-common/1.45.1/) | 1.45.1 | Yes | [Apache-2.0](https://pypi.org/project/opentelemetry-exporter-otlp-proto-common/1.45.1/) |
| [opentelemetry-exporter-otlp-proto-http](https://pypi.org/project/opentelemetry-exporter-otlp-proto-http/1.45.1/) | 1.45.1 | Yes | [Apache-2.0](https://pypi.org/project/opentelemetry-exporter-otlp-proto-http/1.45.1/) |
| [opentelemetry-proto](https://pypi.org/project/opentelemetry-proto/1.45.1/) | 1.45.1 | Yes | [Apache-2.0](https://pypi.org/project/opentelemetry-proto/1.45.1/) |
| [opentelemetry-sdk](https://pypi.org/project/opentelemetry-sdk/1.45.1/) | 1.45.1 | Yes | [Apache-2.0](https://pypi.org/project/opentelemetry-sdk/1.45.1/) |
| [opentelemetry-semantic-conventions](https://pypi.org/project/opentelemetry-semantic-conventions/0.66b1/) | 0.66b1 | Yes | [Apache-2.0](https://pypi.org/project/opentelemetry-semantic-conventions/0.66b1/) |
| [orjson](https://pypi.org/project/orjson/3.13.0/) | 3.13.0 | Yes | [MPL-2.0 AND (Apache-2.0 OR MIT)](https://pypi.org/project/orjson/3.13.0/) |
| [packaging](https://pypi.org/project/packaging/26.3/) | 26.3 | Yes | [Apache-2.0 OR BSD-2-Clause](https://pypi.org/project/packaging/26.3/) |
| [pandas](https://pypi.org/project/pandas/3.0.6/) | 3.0.6 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/pandas/3.0.6/) |
| [pathlib-abc](https://pypi.org/project/pathlib-abc/0.5.2/) | 0.5.2 | Yes | [PSF license](https://pypi.org/project/pathlib-abc/0.5.2/) |
| [pathspec](https://pypi.org/project/pathspec/1.1.1/) | 1.1.1 | Yes | [MPL-2.0](https://pypi.org/project/pathspec/1.1.1/) |
| [pillow](https://pypi.org/project/pillow/12.3.0/) | 12.3.0 | Yes | [MIT-CMU](https://pypi.org/project/pillow/12.3.0/) |
| [platformdirs](https://pypi.org/project/platformdirs/4.13.0/) | 4.13.0 | Yes | [MIT](https://pypi.org/project/platformdirs/4.13.0/) |
| [pluggy](https://pypi.org/project/pluggy/1.6.0/) | 1.6.0 | Yes | [MIT](https://pypi.org/project/pluggy/1.6.0/) |
| [prettytable](https://pypi.org/project/prettytable/3.18.0/) | 3.18.0 | Yes | [BSD-3-Clause](https://pypi.org/project/prettytable/3.18.0/) |
| [propcache](https://pypi.org/project/propcache/0.5.4/) | 0.5.4 | Yes | [Apache-2.0](https://pypi.org/project/propcache/0.5.4/) |
| [protobuf](https://pypi.org/project/protobuf/6.33.6/) | 6.33.6 | Yes | [3-Clause BSD License](https://pypi.org/project/protobuf/6.33.6/) |
| [psutil](https://pypi.org/project/psutil/7.2.2/) | 7.2.2 | Yes | [BSD-3-Clause](https://pypi.org/project/psutil/7.2.2/) |
| [psycopg](https://pypi.org/project/psycopg/3.3.6/) | 3.3.6 | Yes | [LGPL-3.0-only](https://pypi.org/project/psycopg/3.3.6/) |
| [pyarrow](https://pypi.org/project/pyarrow/25.0.1/) | 25.0.1 | Yes | [Apache-2.0](https://pypi.org/project/pyarrow/25.0.1/) |
| [pyasn1](https://pypi.org/project/pyasn1/0.6.4/) | 0.6.4 | Yes | [BSD-2-Clause](https://pypi.org/project/pyasn1/0.6.4/) |
| [pyasn1-modules](https://pypi.org/project/pyasn1-modules/0.4.2/) | 0.4.2 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/pyasn1-modules/0.4.2/) |
| [pycparser](https://pypi.org/project/pycparser/3.11/) | 3.11 | Yes | [BSD-3-Clause](https://pypi.org/project/pycparser/3.11/) |
| [pydantic](https://pypi.org/project/pydantic/2.14.0/) | 2.14.0 | Yes | [MIT](https://pypi.org/project/pydantic/2.14.0/) |
| [pydantic-core](https://pypi.org/project/pydantic-core/2.50.0/) | 2.50.0 | Yes | [MIT](https://pypi.org/project/pydantic-core/2.50.0/) |
| [pydantic-settings](https://pypi.org/project/pydantic-settings/2.15.0/) | 2.15.0 | Yes | [MIT](https://pypi.org/project/pydantic-settings/2.15.0/) |
| [pygments](https://pypi.org/project/pygments/2.21.0/) | 2.21.0 | Yes | [BSD-2-Clause](https://pypi.org/project/pygments/2.21.0/) |
| [pyparsing](https://pypi.org/project/pyparsing/3.3.3/) | 3.3.3 | Yes | [MIT](https://pypi.org/project/pyparsing/3.3.3/) |
| [pytest](https://pypi.org/project/pytest/9.1.1/) | 9.1.1 | Yes | [MIT](https://pypi.org/project/pytest/9.1.1/) |
| [pytest-cov](https://pypi.org/project/pytest-cov/7.1.0/) | 7.1.0 | Yes | [MIT](https://pypi.org/project/pytest-cov/7.1.0/) |
| [python-dateutil](https://pypi.org/project/python-dateutil/2.9.0.post0/) | 2.9.0.post0 | Yes | [Apache-2.0; BSD (maintainer classification; see package license)](https://pypi.org/project/python-dateutil/2.9.0.post0/) |
| [python-dotenv](https://pypi.org/project/python-dotenv/1.2.4/) | 1.2.4 | Yes | [BSD-3-Clause](https://pypi.org/project/python-dotenv/1.2.4/) |
| [pywin32](https://pypi.org/project/pywin32/312/) | 312 | Other platform | [PSF license](https://pypi.org/project/pywin32/312/) |
| [pyyaml](https://pypi.org/project/pyyaml/6.0.3/) | 6.0.3 | Yes | [MIT](https://pypi.org/project/pyyaml/6.0.3/) |
| [referencing](https://pypi.org/project/referencing/0.37.0/) | 0.37.0 | Yes | [MIT](https://pypi.org/project/referencing/0.37.0/) |
| [regex](https://pypi.org/project/regex/2026.9.29/) | 2026.9.29 | Yes | [Apache-2.0 AND CNRI-Python](https://pypi.org/project/regex/2026.9.29/) |
| [requests](https://pypi.org/project/requests/2.34.2/) | 2.34.2 | Yes | [Apache-2.0](https://pypi.org/project/requests/2.34.2/) |
| [rich](https://pypi.org/project/rich/15.0.0/) | 15.0.0 | Yes | [MIT](https://pypi.org/project/rich/15.0.0/) |
| [rpds-py](https://pypi.org/project/rpds-py/2026.9.1/) | 2026.9.1 | Yes | [MIT](https://pypi.org/project/rpds-py/2026.9.1/) |
| [ruff](https://pypi.org/project/ruff/0.17.0/) | 0.17.0 | Yes | [MIT](https://pypi.org/project/ruff/0.17.0/) |
| [s3fs](https://pypi.org/project/s3fs/2026.6.0/) | 2026.6.0 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/s3fs/2026.6.0/) |
| [s3transfer](https://pypi.org/project/s3transfer/0.19.2/) | 0.19.2 | Yes | [Apache-2.0](https://pypi.org/project/s3transfer/0.19.2/) |
| [scikit-learn](https://pypi.org/project/scikit-learn/1.9.1/) | 1.9.1 | Yes | [BSD-3-Clause](https://pypi.org/project/scikit-learn/1.9.1/) |
| [scipy](https://pypi.org/project/scipy/1.18.1/) | 1.18.1 | Yes | [BSD-3-Clause plus bundled notices above](https://pypi.org/project/scipy/1.18.1/) |
| [semver](https://pypi.org/project/semver/3.1.0/) | 3.1.0 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/semver/3.1.0/) |
| [shortuuid](https://pypi.org/project/shortuuid/1.0.13/) | 1.0.13 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/shortuuid/1.0.13/) |
| [six](https://pypi.org/project/six/1.17.0/) | 1.17.0 | Yes | [MIT](https://pypi.org/project/six/1.17.0/) |
| [skops](https://pypi.org/project/skops/0.16.0/) | 0.16.0 | Yes | [MIT](https://github.com/skops-dev/skops/blob/main/LICENSE) |
| [smmap](https://pypi.org/project/smmap/5.0.3/) | 5.0.3 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/smmap/5.0.3/) |
| [sniffio](https://pypi.org/project/sniffio/1.3.1/) | 1.3.1 | Yes | [Apache-2.0; MIT](https://pypi.org/project/sniffio/1.3.1/) |
| [sortedcontainers](https://pypi.org/project/sortedcontainers/2.4.0/) | 2.4.0 | Yes | [Apache-2.0](https://pypi.org/project/sortedcontainers/2.4.0/) |
| [soupsieve](https://pypi.org/project/soupsieve/3.0.1/) | 3.0.1 | Yes | [MIT](https://pypi.org/project/soupsieve/3.0.1/) |
| [sqlalchemy](https://pypi.org/project/sqlalchemy/2.1.4/) | 2.1.4 | Yes | [MIT](https://pypi.org/project/sqlalchemy/2.1.4/) |
| [sqlparse](https://pypi.org/project/sqlparse/0.6.0/) | 0.6.0 | Yes | [BSD (maintainer classification; see package license)](https://pypi.org/project/sqlparse/0.6.0/) |
| [starlette](https://pypi.org/project/starlette/1.7.0/) | 1.7.0 | Yes | [BSD-3-Clause](https://pypi.org/project/starlette/1.7.0/) |
| [tenacity](https://pypi.org/project/tenacity/9.2.1/) | 9.2.1 | Yes | [Apache-2.0](https://pypi.org/project/tenacity/9.2.1/) |
| [textual](https://pypi.org/project/textual/8.2.8/) | 8.2.8 | Yes | [MIT](https://pypi.org/project/textual/8.2.8/) |
| [threadpoolctl](https://pypi.org/project/threadpoolctl/3.7.0/) | 3.7.0 | Yes | [BSD-3-Clause](https://pypi.org/project/threadpoolctl/3.7.0/) |
| [tiktoken](https://pypi.org/project/tiktoken/0.14.0/) | 0.14.0 | Yes | [MIT License](https://pypi.org/project/tiktoken/0.14.0/) |
| [tokenizers](https://pypi.org/project/tokenizers/0.23.3/) | 0.23.3 | Yes | [Apache-2.0](https://pypi.org/project/tokenizers/0.23.3/) |
| [tomlkit](https://pypi.org/project/tomlkit/0.15.1/) | 0.15.1 | Yes | [MIT](https://pypi.org/project/tomlkit/0.15.1/) |
| [tqdm](https://pypi.org/project/tqdm/4.70.1/) | 4.70.1 | Yes | [MPL-2.0 AND MIT](https://pypi.org/project/tqdm/4.70.1/) |
| [trove-classifiers](https://pypi.org/project/trove-classifiers/2026.9.21.13/) | 2026.9.21.13 | Yes | [Apache-2.0](https://pypi.org/project/trove-classifiers/2026.9.21.13/) |
| [typing-extensions](https://pypi.org/project/typing-extensions/4.16.0/) | 4.16.0 | Yes | [PSF-2.0](https://pypi.org/project/typing-extensions/4.16.0/) |
| [typing-inspection](https://pypi.org/project/typing-inspection/0.4.4/) | 0.4.4 | Yes | [MIT](https://pypi.org/project/typing-inspection/0.4.4/) |
| [tzdata](https://pypi.org/project/tzdata/2026.5/) | 2026.5 | Other platform | [Apache-2.0](https://pypi.org/project/tzdata/2026.5/) |
| [universal-pathlib](https://pypi.org/project/universal-pathlib/0.3.10/) | 0.3.10 | Yes | [MIT](https://pypi.org/project/universal-pathlib/0.3.10/) |
| [urllib3](https://pypi.org/project/urllib3/2.8.0/) | 2.8.0 | Yes | [MIT](https://pypi.org/project/urllib3/2.8.0/) |
| [uvicorn](https://pypi.org/project/uvicorn/0.54.0/) | 0.54.0 | Yes | [BSD-3-Clause](https://pypi.org/project/uvicorn/0.54.0/) |
| [waitress](https://pypi.org/project/waitress/3.0.2/) | 3.0.2 | Other platform | [ZPL license](https://pypi.org/project/waitress/3.0.2/) |
| [wcwidth](https://pypi.org/project/wcwidth/0.9.2/) | 0.9.2 | Yes | [MIT](https://pypi.org/project/wcwidth/0.9.2/) |
| [werkzeug](https://pypi.org/project/werkzeug/3.1.9/) | 3.1.9 | Yes | [BSD-3-Clause](https://pypi.org/project/werkzeug/3.1.9/) |
| [wrapt](https://pypi.org/project/wrapt/2.5.0/) | 2.5.0 | Yes | [BSD-2-Clause](https://pypi.org/project/wrapt/2.5.0/) |
| [yarl](https://pypi.org/project/yarl/1.25.1/) | 1.25.1 | Yes | [Apache-2.0](https://pypi.org/project/yarl/1.25.1/) |
| [zipfile-zstd](https://pypi.org/project/zipfile-zstd/0.0.4/) | 0.0.4 | Yes | [MIT](https://pypi.org/project/zipfile-zstd/0.0.4/) |
| [zipp](https://pypi.org/project/zipp/4.1.1/) | 4.1.1 | Yes | [MIT](https://pypi.org/project/zipp/4.1.1/) |
| [zstandard](https://pypi.org/project/zstandard/0.25.0/) | 0.25.0 | Yes | [BSD-3-Clause](https://pypi.org/project/zstandard/0.25.0/) |

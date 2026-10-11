# Project instructions

This project currently contains a scaffold only. Follow the user's requested
phase; do not infer authorization to implement features from the roadmap.

Before installing any dependency, present its library name and license and
obtain the user's approval. The current proposal is in `docs/dependencies.md`.
This applies to build/development tools and service/model downloads as well as
runtime libraries. Approval for environment setup alone does not authorize
feature implementation.

Use Python 3.12 conventions and the tool configuration in `pyproject.toml`.
Keep tests under the top-level `tests/` directory. Do not import from or modify
sibling projects as an implicit part of this scaffold.

For documentation, explain the purpose before mechanics, use concrete examples,
and label hypothetical outcomes. Distinguish planned requirements from working
behavior and measured results. Keep ADR status accurate and local links valid.

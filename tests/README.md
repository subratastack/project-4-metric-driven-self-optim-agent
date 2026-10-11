# Test placeholders

No feature tests exist because no features are implemented. The directories
reserve the guided build's unit, integration, evaluation, optimization,
adversarial, and regression suites. Test discovery is configured in
`pyproject.toml` for this top-level `tests/` tree.

Do not treat empty test collection as a passing behavioral test suite. Future
integration/evaluation tests must explicitly opt into local services and model
calls; ordinary unit tests should not start services or download models.

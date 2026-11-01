# Phase 1 tests

Run from the project directory with `.venv/bin/python -m pytest -q`.
The suite uses only the installed development dependencies and performs no model
inference, service startup, network request, tool execution or optimizer call.

- `unit/test_contracts.py`: strict JSON, identifiers, timestamps, references,
  fingerprints, output unions and label-free rendering.
- `unit/test_baseline.py`: single-call profile, token preflight, timeout, no repair,
  unsafe partial output, missing usage, model identity and artifact integrity.
- `unit/test_model_strategy.py`: file-only provider/model selection, interchangeable
  transports, remote routing restrictions, sanitized errors, deadlines and usage.
  All OpenRouter responses are mocked; no API key or network is needed.
- `evaluation/test_dataset.py`: all 100 case round trips, deterministic rebuilds,
  review admission, split/source isolation, conflicting labels and corrupted bytes.
- `evaluation/test_scorers.py`: exact labels, evidence support, denied/unknown
  actions, hidden forbidden decisions, repetition and failed-attempt denominators.
- `evaluation/test_runner.py`: complete and interrupted runs, persisted observations,
  bounded accounting, holdout-inference refusal and backend-contract violations.

`FakeBackend` and `AbstainBackend` are explicit test doubles. Their outputs and
usage counts exercise code paths; they are not measurements of a local model.
Feeding expected decisions into a scorer tests the scorer against its labels;
it does not independently validate the semantic quality of those labels.

The Ollama/tokenizer unit tests use synthetic vocabulary fixtures and mocked
HTTP responses. Real inference is an explicit opt-in through
`python -m scripts.verify_qwen3`; see the measured
[local verification](../docs/qwen3-local-verification.md). The optimization, adversarial and regression directories retain their
reserved structure; adversarial protocol cases currently live in the unit and
evaluation tests listed above.

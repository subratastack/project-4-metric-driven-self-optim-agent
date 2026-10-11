# Guided build roadmap

This is a reference to the [Notion brief](https://app.notion.com/p/3e8456c5513581f89164d6f511de8f70),
not an implementation checklist authorized for execution. Phase 0 documentation
is finalized in the [review record](phase-0-review.md). All implementation phases
remain pending; no optimizer or feature is authorized by this roadmap alone.

| Phase | Future work | Review gate |
| --- | --- | --- |
| 0 | Optimization contract — documentation complete | Architecture, accepted ADRs, dataset schema, metric definitions and frozen baseline contract recorded; executable artifacts remain pending |
| 1 | Frozen baseline and 50–100 cases | Reproducible baseline, deterministic scorers, isolated splits |
| 2 | DSPy decision program | Preserve runtime contracts |
| 3 | MLflow evaluation | Reconstruct runs from tracked evidence |
| 4 | Reliability and statistics | Paired repeated runs and uncertainty |
| 5 | Optimizer-facing metric | Hard constraints survive scalarization |
| 6 | Calibrated local judge | Human agreement and documented limitations |
| 7 | MIPROv2 | Development improvement within constraints |
| 8 | Promotion control plane | Immutable candidates and gated activation/rollback |
| 9 | GEPA | Compare with MIPROv2 on the same holdout |
| 10 | Inspect AI | Explain discrepancies with primary evaluation |
| 11 | Optuna Pareto experiment | Identify dominated configurations |
| 12 | Goodhart experiment | Demonstrate and repair a gameable objective |
| 13 | TextGrad comparison | Compare isolated textual optimization |
| 14 | Optional Ax/BoTorch | Justify added search complexity |
| 15 | Ablation | Isolate which component caused improvement |
| 16 | Frozen final test | Test and adversarial results, uncertainty, usage, rollback artifact |

Later failure tests must cover unsafe score improvements, development overfit,
judge/oracle disagreement, judge changes, interrupted optimization, dataset
mutation, exhausted evaluation/token budgets, and unstable metric weights.

The optional Jev/Kev evaluator extension is deferred. No package or hosted
service is selected for it. DoWhy is also deferred until there is a concrete
causal question and enough experiment data. Neither is an initial dependency.

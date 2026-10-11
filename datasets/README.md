# Dataset placeholders

`manifests/` will describe immutable versions, hashes, provenance, and split
membership. `fixtures/` will hold small reviewed examples. Both are empty.

The v1 splits are train, development/validation (`dev`), frozen test, and
adversarial holdout (`adversarial`), targeting 40/20/20/20 cases grouped by
incident lineage. The [dataset schema](../docs/dataset-schema.md) defines Case
and Manifest records and validation rules. It is documentation, not an
implemented validator or a released dataset.

No case artifacts, manifests, split assignments, or loaders exist yet. The
public documentation example may become a train fixture, never a hidden
holdout. See [ADR-003](../docs/adr/003-dataset-splits-and-leakage.md).

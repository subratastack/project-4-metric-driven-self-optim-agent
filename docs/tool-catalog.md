# Synthetic incident tool catalogue v1

`incident-tools-v1` gives the dataset validator concrete tool names, argument
schemas and effects. These are runtime-supplied **options**, not executable tool
functions. The decision model selects an action ID; it never supplies arguments.
The catalogue is implemented in `apps/decision_program/tool_catalog.py`.

All argument objects reject unknown fields and coercion. Every tool requires
`service`, a nonempty string of at most 128 characters. Additional arguments:

| Tool | Additional required arguments | Effect |
| --- | --- | --- |
| `read_metric` | `metric`: string 1–128; `window_seconds`: integer 1–86400 | read_only |
| `read_logs` | `filter`: string 1–256; `window_seconds`: integer 1–86400 | read_only |
| `read_config` | `key`: string 1–128 | read_only |
| `read_dependency` | `dependency`: string 1–128 | read_only |
| `read_deployments` | none | read_only |
| `read_trace` | `operation`: string 1–128 | read_only |
| `restart_service` | none | mutating |
| `rollback_deployment` | `revision`: string 1–128 | mutating |
| `scale_service` | `replicas`: integer 1–100 | mutating |

`runtime-policy-v1` requires authorization `allow`, approval `not_required` or
`granted`, present evidence prerequisites, one available call and enough remaining
tool time for the option's estimate. This catalogue requires explicit approval
for every mutating tool: `not_required` is invalid for those options. A denied
option may appear in a snapshot, but selecting it is unsafe regardless of approval.
Read-only options can also be denied or require approval. Descriptions, evidence
and incident text cannot change these fields.

Argument validation, an action fingerprint, or a prompt instruction is not live
execution authorization. A future runtime adapter must reauthorize against its
current policy and preserve fixed arguments and idempotency before dispatch.
No such adapter or actual diagnostic/remediation operation is implemented here.

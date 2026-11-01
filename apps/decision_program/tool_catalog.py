"""Versioned synthetic runtime tool schemas; this module never executes tools."""

from typing import Any

from pydantic import Field

from apps.decision_program.signature import ActionOption, Contract

TOOL_CATALOG_VERSION = "incident-tools-v1"
RUNTIME_POLICY_VERSION = "runtime-policy-v1"


class ServiceArgs(Contract):
    service: str = Field(min_length=1, max_length=128)


class MetricArgs(ServiceArgs):
    metric: str = Field(min_length=1, max_length=128)
    window_seconds: int = Field(ge=1, le=86400)


class LogsArgs(ServiceArgs):
    filter: str = Field(min_length=1, max_length=256)
    window_seconds: int = Field(ge=1, le=86400)


class ConfigArgs(ServiceArgs):
    key: str = Field(min_length=1, max_length=128)


class DependencyArgs(ServiceArgs):
    dependency: str = Field(min_length=1, max_length=128)


class TraceArgs(ServiceArgs):
    operation: str = Field(min_length=1, max_length=128)


class RollbackArgs(ServiceArgs):
    revision: str = Field(min_length=1, max_length=128)


class ScaleArgs(ServiceArgs):
    replicas: int = Field(ge=1, le=100)


TOOL_SCHEMAS: dict[str, tuple[type[Contract], str]] = {
    "read_metric": (MetricArgs, "read_only"),
    "read_logs": (LogsArgs, "read_only"),
    "read_config": (ConfigArgs, "read_only"),
    "read_dependency": (DependencyArgs, "read_only"),
    "read_deployments": (ServiceArgs, "read_only"),
    "read_trace": (TraceArgs, "read_only"),
    "restart_service": (ServiceArgs, "mutating"),
    "rollback_deployment": (RollbackArgs, "mutating"),
    "scale_service": (ScaleArgs, "mutating"),
}


def validate_tool(action: ActionOption) -> None:
    if action.tool_name not in TOOL_SCHEMAS:
        raise ValueError(f"unknown tool: {action.tool_name}")
    schema, effect = TOOL_SCHEMAS[action.tool_name]
    schema.model_validate(action.arguments)
    if action.effect != effect:
        raise ValueError("tool effect does not match catalogue")
    if effect == "mutating" and action.approval == "not_required":
        raise ValueError("this catalogue requires approval for mutating tools")


def catalog_contract() -> dict[str, Any]:
    return {
        name: {"effect": effect, "arguments": schema.model_json_schema()}
        for name, (schema, effect) in sorted(TOOL_SCHEMAS.items())
    }

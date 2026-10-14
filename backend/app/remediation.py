from dataclasses import dataclass

from app.connectors import (
    connector_registry,
)


@dataclass(frozen=True)
class RemediationAction:
    key: str
    target_service: str
    connector_key: str
    description: str
    risk_level: str


REMEDIATION_CATALOG = {
    "restart_benchmark_redis":
        RemediationAction(
            key=(
                "restart_benchmark_redis"
            ),
            target_service=(
                "benchmark-redis"
            ),
            connector_key=(
                "benchmark"
            ),
            description=(
                "Restart the benchmark "
                "Redis container"
            ),
            risk_level="MEDIUM",
        ),

    "restart_benchmark_postgresql":
        RemediationAction(
            key=(
                "restart_benchmark_postgresql"
            ),
            target_service=(
                "benchmark-postgresql"
            ),
            connector_key=(
                "benchmark"
            ),
            description=(
                "Restart the benchmark "
                "PostgreSQL container"
            ),
            risk_level="HIGH",
        ),

    "restart_benchmark_api":
        RemediationAction(
            key=(
                "restart_benchmark_api"
            ),
            target_service=(
                "benchmark-api"
            ),
            connector_key=(
                "benchmark"
            ),
            description=(
                "Restart the benchmark "
                "API container"
            ),
            risk_level="MEDIUM",
        ),
}


def execute_remediation_action(
    action_key: str,
) -> dict:
    action = (
        REMEDIATION_CATALOG.get(
            action_key
        )
    )

    if action is None:
        raise ValueError(
            (
                "Unsupported remediation "
                f"action: {action_key}"
            )
        )

    connector = (
        connector_registry.resolve(
            connector_key=(
                action.connector_key
            ),
            service=(
                action.target_service
            ),
        )
    )

    result = (
        connector.execute_action(
            action_key=(
                action.key
            ),
            target_service=(
                action.target_service
            ),
        )
    )

    return {
        "success":
            result.success,

        "exit_code":
            result.exit_code,

        "stdout":
            result.stdout,

        "stderr":
            result.stderr,

        "connector":
            result.connector,

        "action_key":
            result.action_key,

        "target_service":
            result.target_service,
    }
from dataclasses import dataclass


@dataclass(frozen=True)
class RemediationAction:
    key: str
    target_service: str
    compose_service: str
    description: str
    risk_level: str


REMEDIATION_CATALOG = {
    "restart_benchmark_redis": RemediationAction(
        key="restart_benchmark_redis",
        target_service="benchmark-redis",
        compose_service="benchmark-redis",
        description="Restart the benchmark Redis container",
        risk_level="MEDIUM",
    ),
    "restart_benchmark_postgresql": RemediationAction(
        key="restart_benchmark_postgresql",
        target_service="benchmark-postgresql",
        compose_service="benchmark-db",
        description="Restart the benchmark PostgreSQL container",
        risk_level="HIGH",
    ),
    "restart_benchmark_api": RemediationAction(
        key="restart_benchmark_api",
        target_service="benchmark-api",
        compose_service="benchmark-api",
        description="Restart the benchmark API container",
        risk_level="MEDIUM",
    ),
}

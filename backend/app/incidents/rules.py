from dataclasses import dataclass
from enum import Enum


class Severity(
    str,
    Enum,
):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Operator(
    str,
    Enum,
):
    LESS_THAN = "lt"
    GREATER_THAN = "gt"
    EQUAL = "eq"


@dataclass(frozen=True)
class IncidentRule:
    key: str
    title: str
    service: str
    connector_key: str
    severity: Severity
    operator: Operator
    threshold: float

    def is_triggered(
        self,
        value: float,
    ) -> bool:
        if (
            self.operator
            == Operator.LESS_THAN
        ):
            return (
                value
                < self.threshold
            )

        if (
            self.operator
            == Operator.GREATER_THAN
        ):
            return (
                value
                > self.threshold
            )

        if (
            self.operator
            == Operator.EQUAL
        ):
            return (
                value
                == self.threshold
            )

        return False


INCIDENT_RULES = [
    IncidentRule(
        key=(
            "postgresql_unavailable"
        ),
        title=(
            "Benchmark PostgreSQL "
            "unavailable"
        ),
        service=(
            "benchmark-postgresql"
        ),
        connector_key="benchmark",
        severity=Severity.HIGH,
        operator=Operator.EQUAL,
        threshold=0,
    ),

    IncidentRule(
        key=(
            "redis_unavailable"
        ),
        title=(
            "Benchmark Redis unavailable"
        ),
        service=(
            "benchmark-redis"
        ),
        connector_key="benchmark",
        severity=Severity.HIGH,
        operator=Operator.EQUAL,
        threshold=0,
    ),

    IncidentRule(
        key=(
            "http_5xx_rate_high"
        ),
        title=(
            "Benchmark API elevated "
            "HTTP 5xx rate"
        ),
        service=(
            "benchmark-api"
        ),
        connector_key="benchmark",
        severity=Severity.MEDIUM,
        operator=(
            Operator.GREATER_THAN
        ),
        threshold=0.05,
    ),

    IncidentRule(
        key=(
            "api_latency_high"
        ),
        title=(
            "Benchmark API high "
            "P95 latency"
        ),
        service=(
            "benchmark-api"
        ),
        connector_key="benchmark",
        severity=Severity.MEDIUM,
        operator=(
            Operator.GREATER_THAN
        ),
        threshold=2.0,
    ),
]
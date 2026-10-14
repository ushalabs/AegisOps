from dataclasses import dataclass
from typing import Optional

from app.connectors import (
    ConnectorStatus,
    connector_registry,
)
from app.incidents.rules import (
    INCIDENT_RULES,
    IncidentRule,
)


@dataclass
class DetectionResult:
    rule_key: str
    title: str
    service: str
    severity: str
    triggered: bool
    value: Optional[float]
    threshold: float


def evaluate_rule(
    rule: IncidentRule,
) -> DetectionResult:
    connector = (
        connector_registry.resolve(
            connector_key=(
                rule.connector_key
            ),
            service=(
                rule.service
            ),
        )
    )

    signal = connector.get_signal(
        signal_key=rule.key,
        service=rule.service,
    )

    if (
        signal.status
        != ConnectorStatus.OK
    ):
        return DetectionResult(
            rule_key=rule.key,
            title=rule.title,
            service=rule.service,
            severity=(
                rule.severity.value
            ),
            triggered=False,
            value=None,
            threshold=rule.threshold,
        )

    value = signal.first_value

    if value is None:
        return DetectionResult(
            rule_key=rule.key,
            title=rule.title,
            service=rule.service,
            severity=(
                rule.severity.value
            ),
            triggered=False,
            value=None,
            threshold=rule.threshold,
        )

    return DetectionResult(
        rule_key=rule.key,
        title=rule.title,
        service=rule.service,
        severity=(
            rule.severity.value
        ),
        triggered=(
            rule.is_triggered(
                value
            )
        ),
        value=value,
        threshold=rule.threshold,
    )


def evaluate_all_rules(
) -> list[DetectionResult]:
    return [
        evaluate_rule(
            rule
        )
        for rule
        in INCIDENT_RULES
    ]
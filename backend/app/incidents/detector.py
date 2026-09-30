from dataclasses import dataclass
from typing import Optional

from app.incidents.rules import INCIDENT_RULES, IncidentRule
from app.monitoring.prometheus import (
    PrometheusError,
    prometheus_client,
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


def extract_metric_value(result: list[dict]) -> Optional[float]:
    if not result:
        return None

    try:
        raw_value = result[0]["value"][1]
        return float(raw_value)

    except (KeyError, IndexError, TypeError, ValueError):
        return None


def evaluate_rule(rule: IncidentRule) -> DetectionResult:
    try:
        result = prometheus_client.query(rule.promql)
        value = extract_metric_value(result)

    except PrometheusError:
        return DetectionResult(
            rule_key=rule.key,
            title=rule.title,
            service=rule.service,
            severity=rule.severity.value,
            triggered=False,
            value=None,
            threshold=rule.threshold,
        )

    if value is None:
        return DetectionResult(
            rule_key=rule.key,
            title=rule.title,
            service=rule.service,
            severity=rule.severity.value,
            triggered=False,
            value=None,
            threshold=rule.threshold,
        )

    return DetectionResult(
        rule_key=rule.key,
        title=rule.title,
        service=rule.service,
        severity=rule.severity.value,
        triggered=rule.is_triggered(value),
        value=value,
        threshold=rule.threshold,
    )


def evaluate_all_rules() -> list[DetectionResult]:
    return [
        evaluate_rule(rule)
        for rule in INCIDENT_RULES
    ]
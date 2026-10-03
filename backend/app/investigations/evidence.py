
from datetime import datetime, timezone
from math import isfinite

from app.incidents.repository import get_incident_by_id
from app.incidents.rules import INCIDENT_RULES
from app.monitoring.prometheus import (
    PrometheusError,
    prometheus_client,
)


def collect_incident_evidence(incident_id: int) -> dict:
    row = get_incident_by_id(incident_id)

    if row is None:
        raise ValueError(f"Incident {incident_id} not found")

    incident = {
        "id": row[0],
        "fingerprint": row[1],
        "rule_key": row[2],
        "title": row[3],
        "service": row[4],
        "severity": row[5],
        "status": row[6],
        "trigger_value": row[7],
        "threshold": row[8],
        "first_detected_at": row[9].isoformat(),
        "last_seen_at": row[10].isoformat(),
        "resolved_at": (
            row[11].isoformat() if row[11] else None
        ),
    }

    collected_at = datetime.now(timezone.utc).isoformat()
    signals = {}

    for rule in INCIDENT_RULES:
        signal = {
            "title": rule.title,
            "service": rule.service,
            "query": rule.promql,
            "threshold": rule.threshold,
            "operator": rule.operator.value,
            "readings": [],
        }

        try:
            results = prometheus_client.query(rule.promql)

            for result in results:
                sample = result.get("value", [])

                if len(sample) != 2:
                    continue

                value = float(sample[1])

                if not isfinite(value):
                    continue

                signal["readings"].append({
                    "labels": result.get("metric", {}),
                    "value": value,
                    "sample_time": datetime.fromtimestamp(
                        float(sample[0]),
                        tz=timezone.utc,
                    ).isoformat(),
                })

            signal["data_status"] = (
                "AVAILABLE"
                if signal["readings"]
                else "NO_DATA"
            )

        except PrometheusError as exc:
            signal["data_status"] = "QUERY_ERROR"
            signal["error"] = str(exc)

        signals[rule.key] = signal

    return {
        "incident": incident,
        "evidence_collected_at": collected_at,
        "evidence_type": "CURRENT_METRIC_SNAPSHOT",
        "monitoring_signals": signals,
    }

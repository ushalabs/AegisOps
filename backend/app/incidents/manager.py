from app.incidents.detector import (
    DetectionResult,
    evaluate_all_rules,
)
from app.incidents.repository import (
    build_fingerprint,
    create_incident,
    get_open_incident,
    resolve_incident,
    update_incident_last_seen,
)

from app.orchestration.n8n import notify_incident_created


def process_detection_result(result: DetectionResult) -> dict:
    fingerprint = build_fingerprint(result)

    # value=None means the rule could not be evaluated.
    # Do not create OR resolve incidents from unknown telemetry.
    if result.value is None:
        return {
            "rule_key": result.rule_key,
            "action": "SKIPPED",
            "reason": "metric unavailable",
        }

    open_incident = get_open_incident(fingerprint)

    if result.triggered:
        if open_incident:
            update_incident_last_seen(
                fingerprint=fingerprint,
                trigger_value=result.value,
            )

            return {
                "rule_key": result.rule_key,
                "action": "UPDATED",
                "incident_id": open_incident[0],
            }

        incident_id = create_incident(result)

        notify_incident_created(
            incident_id=incident_id,
            result=result,
        )

        return {
            "rule_key": result.rule_key,
            "action": "CREATED",
            "incident_id": incident_id,
        }

    if open_incident:
        resolve_incident(fingerprint)

        return {
            "rule_key": result.rule_key,
            "action": "RESOLVED",
            "incident_id": open_incident[0],
        }

    return {
        "rule_key": result.rule_key,
        "action": "HEALTHY",
    }

    if open_incident:
        resolve_incident(fingerprint)

        return {
            "rule_key": result.rule_key,
            "action": "RESOLVED",
            "incident_id": open_incident[0],
        }

    return {
        "rule_key": result.rule_key,
        "action": "HEALTHY",
    }


def run_detection_cycle() -> list[dict]:
    results = evaluate_all_rules()

    return [
        process_detection_result(result)
        for result in results
    ]
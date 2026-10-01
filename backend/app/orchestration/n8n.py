import logging

import httpx

from app.core.config import settings
from app.incidents.detector import DetectionResult

logger = logging.getLogger(__name__)


def notify_incident_created(
    incident_id: int,
    result: DetectionResult,
) -> None:
    payload = {
        "incident_id": incident_id,
        "rule_key": result.rule_key,
        "title": result.title,
        "service": result.service,
        "severity": result.severity,
        "status": "OPEN",
        "trigger_value": result.value,
        "threshold": result.threshold,
    }

    try:
        response = httpx.post(
            settings.n8n_incident_webhook_url,
            json=payload,
            timeout=5.0,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception(
            "Failed to notify n8n for incident %s",
            incident_id,
        )

import logging

import psycopg
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.investigations.evidence import collect_incident_evidence
from app.investigations.gemini_client import investigate_with_gemini
from app.investigations.repository import save_investigation
from fastapi import Query

from app.investigations.repository import (
    save_investigation,
    get_investigation_by_id,
    list_investigations_for_incident,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/investigations",
    tags=["investigations"],
)



@router.post("/{incident_id}/run")
def run_investigation(incident_id: int):
    try:
        evidence = collect_incident_evidence(incident_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Incident database unavailable",
        ) from exc

    if evidence["incident"]["status"] != "OPEN":
        raise HTTPException(
            status_code=409,
            detail="Only OPEN incidents can be investigated",
        )

    # Step 1: Generate the Gemini investigation.
    try:
        report = investigate_with_gemini(evidence)
    except Exception as exc:
        logger.exception(
            "Gemini investigation failed for incident %s",
            incident_id,
        )
        raise HTTPException(
            status_code=502,
            detail="Gemini investigation failed; check backend logs",
        ) from exc

    # Step 2: Save the report and its supporting evidence.
    try:
        investigation_id = save_investigation(
            incident_id=incident_id,
            model=settings.gemini_model,
            evidence=evidence,
            report=report,
        )
    except psycopg.Error as exc:
        logger.exception(
            "Failed to save investigation for incident %s",
            incident_id,
        )
        raise HTTPException(
            status_code=503,
            detail="Investigation generated but could not be saved",
        ) from exc

    # Step 3: Return the persisted investigation.
    return {
        "investigation_id": investigation_id,
        "incident_id": incident_id,
        "model": settings.gemini_model,
        "evidence_collected_at": evidence["evidence_collected_at"],
        "investigation": report.model_dump(mode="json"),
    }


@router.get("/by-incident/{incident_id}")
def get_incident_investigations(
    incident_id: int,
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        investigations = list_investigations_for_incident(
            incident_id=incident_id,
            limit=limit,
        )
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Investigation database unavailable",
        ) from exc

    return {
        "incident_id": incident_id,
        "count": len(investigations),
        "investigations": investigations,
    }


@router.get("/{investigation_id}")
def get_investigation(investigation_id: int):
    try:
        investigation = get_investigation_by_id(
            investigation_id
        )
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Investigation database unavailable",
        ) from exc

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    return investigation
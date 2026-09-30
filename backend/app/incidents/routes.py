import psycopg
from fastapi import APIRouter, HTTPException

from app.db.database import get_connection
from app.incidents.manager import run_detection_cycle


router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)


@router.post("/detect")
def run_incident_detection():
    try:
        results = run_detection_cycle()

        return {
            "status": "completed",
            "results": results,
        }

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Incident database operation failed: {exc}",
        ) from exc


@router.get("")
def list_incidents():
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        fingerprint,
                        rule_key,
                        title,
                        service,
                        severity,
                        status,
                        trigger_value,
                        threshold,
                        first_detected_at,
                        last_seen_at,
                        resolved_at
                    FROM incidents
                    ORDER BY first_detected_at DESC;
                    """
                )

                rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "fingerprint": row[1],
                "rule_key": row[2],
                "title": row[3],
                "service": row[4],
                "severity": row[5],
                "status": row[6],
                "trigger_value": row[7],
                "threshold": row[8],
                "first_detected_at": row[9],
                "last_seen_at": row[10],
                "resolved_at": row[11],
            }
            for row in rows
        ]

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to retrieve incidents: {exc}",
        ) from exc
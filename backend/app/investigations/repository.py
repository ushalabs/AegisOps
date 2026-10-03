
from datetime import datetime

from psycopg.types.json import Jsonb

from app.db.database import get_connection
from app.investigations.schemas import InvestigationReport


def save_investigation(
    incident_id: int,
    model: str,
    evidence: dict,
    report: InvestigationReport,
) -> int:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO investigations (
                    incident_id,
                    model,
                    evidence_collected_at,
                    evidence,
                    report
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    incident_id,
                    model,
                    datetime.fromisoformat(
                        evidence["evidence_collected_at"]
                    ),
                    Jsonb(evidence),
                    Jsonb(report.model_dump(mode="json")),
                ),
            )

            row = cursor.fetchone()
            return row[0]


def get_investigation_by_id(investigation_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    incident_id,
                    model,
                    evidence_collected_at,
                    evidence,
                    report,
                    created_at
                FROM investigations
                WHERE id = %s;
                """,
                (investigation_id,),
            )

            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "incident_id": row[1],
        "model": row[2],
        "evidence_collected_at": row[3],
        "evidence": row[4],
        "report": row[5],
        "created_at": row[6],
    }


def list_investigations_for_incident(
    incident_id: int,
    limit: int = 20,
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    incident_id,
                    model,
                    report->>'summary',
                    report->>'confidence',
                    created_at
                FROM investigations
                WHERE incident_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s;
                """,
                (incident_id, limit),
            )

            rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "incident_id": row[1],
            "model": row[2],
            "summary": row[3],
            "confidence": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]

from app.db.database import get_connection
from app.incidents.detector import DetectionResult


def build_fingerprint(result: DetectionResult) -> str:
    return f"{result.service}:{result.rule_key}"


def get_open_incident(fingerprint: str):
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
                WHERE fingerprint = %s
                  AND status = 'OPEN'
                LIMIT 1;
                """,
                (fingerprint,),
            )

            return cursor.fetchone()


def create_incident(result: DetectionResult):
    fingerprint = build_fingerprint(result)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO incidents (
                    fingerprint,
                    rule_key,
                    title,
                    service,
                    severity,
                    trigger_value,
                    threshold
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    fingerprint,
                    result.rule_key,
                    result.title,
                    result.service,
                    result.severity,
                    result.value,
                    result.threshold,
                ),
            )

            row = cursor.fetchone()

    return row[0]


def update_incident_last_seen(
    fingerprint: str,
    trigger_value: float | None,
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE incidents
                SET
                    last_seen_at = NOW(),
                    trigger_value = %s
                WHERE fingerprint = %s
                  AND status = 'OPEN';
                """,
                (
                    trigger_value,
                    fingerprint,
                ),
            )


def resolve_incident(fingerprint: str):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = 'RESOLVED',
                    resolved_at = NOW(),
                    last_seen_at = NOW()
                WHERE fingerprint = %s
                  AND status = 'OPEN';
                """,
                (fingerprint,),
            )

def get_incident_by_id(incident_id: int):
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
                WHERE id = %s
                LIMIT 1;
                """,
                (incident_id,),
            )

            return cursor.fetchone()
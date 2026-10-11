from typing import Any

from psycopg.types.json import Jsonb

from app.db.database import (
    get_connection,
)


def create_eval_run(
    suite_name: str,
    total_cases: int,
    metadata: dict[str, Any] | None = None,
) -> int:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO eval_runs (
                    suite_name,
                    status,
                    total_cases,
                    metadata
                )
                VALUES (
                    %s,
                    'RUNNING',
                    %s,
                    %s
                )
                RETURNING id;
                """,
                (
                    suite_name,
                    total_cases,
                    Jsonb(
                        metadata or {}
                    ),
                ),
            )

            row = cursor.fetchone()

    return row[0]


def save_eval_result(
    eval_run_id: int,
    result: dict[str, Any],
) -> int:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO eval_results (
                    eval_run_id,
                    incident_id,
                    investigation_id,
                    case_key,
                    passed,
                    score,
                    checks
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id;
                """,
                (
                    eval_run_id,
                    result["incident_id"],
                    result["investigation_id"],
                    result["case_key"],
                    result["passed"],
                    result["score"],
                    Jsonb(
                        result["checks"]
                    ),
                ),
            )

            row = cursor.fetchone()

    return row[0]


def finish_eval_run(
    eval_run_id: int,
    passed_cases: int,
    failed_cases: int,
    status: str = "COMPLETED",
) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE eval_runs
                SET
                    status = %s,
                    passed_cases = %s,
                    failed_cases = %s,
                    finished_at = NOW()
                WHERE id = %s;
                """,
                (
                    status,
                    passed_cases,
                    failed_cases,
                    eval_run_id,
                ),
            )
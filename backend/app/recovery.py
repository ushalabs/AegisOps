from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from app.incidents.repository import resolve_incident
from app.db.database import get_connection
from app.incidents.detector import evaluate_rule
from app.incidents.rules import (
    INCIDENT_RULES,
    IncidentRule,
)


MAX_RECOVERY_ATTEMPTS = 3
REQUIRED_HEALTHY_CHECKS = 2

TERMINAL_RECOVERY_STATUSES = {
    "RECOVERED",
    "NOT_RECOVERED",
    "INCONCLUSIVE",
}


@dataclass(frozen=True)
class RecoveryObservation:
    rule_key: str
    service: str
    healthy: bool | None
    triggered: bool | None
    observed_value: float | None
    threshold: float
    telemetry_available: bool


def get_incident_rule(
    rule_key: str,
) -> IncidentRule | None:
    for rule in INCIDENT_RULES:
        if rule.key == rule_key:
            return rule

    return None


def evaluate_recovery(
    rule_key: str,
) -> RecoveryObservation:
    rule = get_incident_rule(rule_key)

    if rule is None:
        raise ValueError(
            f"Unknown incident rule: {rule_key}"
        )

    result = evaluate_rule(rule)

    if result.value is None:
        return RecoveryObservation(
            rule_key=rule.key,
            service=rule.service,
            healthy=None,
            triggered=None,
            observed_value=None,
            threshold=rule.threshold,
            telemetry_available=False,
        )

    return RecoveryObservation(
        rule_key=rule.key,
        service=rule.service,
        healthy=not result.triggered,
        triggered=result.triggered,
        observed_value=result.value,
        threshold=rule.threshold,
        telemetry_available=True,
    )


def _get_execution_context(
    execution_id: int,
) -> dict:
    with get_connection() as conn:
        with conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                """
                SELECT
                    re.id AS execution_id,
                    re.proposal_id,
                    re.incident_id,
                    re.status AS execution_status,
                    re.action_key,
                    re.target_service,
                    i.rule_key,
                    i.fingerprint,
                    i.status AS incident_status
                FROM remediation_executions AS re
                JOIN incidents AS i
                    ON i.id = re.incident_id
                WHERE re.id = %s
                """,
                (execution_id,),
            )

            record = cur.fetchone()

    if record is None:
        raise ValueError(
            "Remediation execution not found."
        )

    if record["execution_status"] != "SUCCEEDED":
        raise ValueError(
            "Recovery can only be verified after "
            "a SUCCEEDED remediation execution."
        )

    return record


def _get_existing_verification(
    execution_id: int,
) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM recovery_verifications
                WHERE execution_id = %s
                """,
                (execution_id,),
            )

            return cur.fetchone()


def verify_recovery_attempt(
    execution_id: int,
) -> dict:
    context = _get_execution_context(
        execution_id
    )

    existing = _get_existing_verification(
        execution_id
    )

    if (
        existing is not None
        and existing["status"]
        in TERMINAL_RECOVERY_STATUSES
    ):
        if existing["status"] == "RECOVERED":
            _ensure_incident_resolved(
                context["fingerprint"]
            )

        return {
            **existing,
            "healthy_now": (
                existing["status"]
                == "RECOVERED"
            ),
            "should_retry": False,
            "reused": True,
        }

        return {
            **existing,
            "healthy_now": (
                existing["status"]
                == "RECOVERED"
            ),
            "should_retry": False,
            "reused": True,
        }

    rule = get_incident_rule(
        context["rule_key"]
    )

    if rule is None:
        raise ValueError(
            "Incident references an unknown rule."
        )

    # Prometheus is queried outside the database
    # transaction so an external request does not
    # hold database locks.
    observation = evaluate_recovery(
        context["rule_key"]
    )

    checked_at = datetime.now(
        timezone.utc
    )

    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

                # Ensure exactly one verification
                # lifecycle exists per execution.
                cur.execute(
                    """
                    INSERT INTO recovery_verifications (
                        execution_id,
                        incident_id,
                        rule_key
                    )
                    VALUES (%s, %s, %s)
                    ON CONFLICT (execution_id)
                    DO NOTHING
                    """,
                    (
                        execution_id,
                        context["incident_id"],
                        context["rule_key"],
                    ),
                )

                cur.execute(
                    """
                    SELECT *
                    FROM recovery_verifications
                    WHERE execution_id = %s
                    FOR UPDATE
                    """,
                    (execution_id,),
                )

                verification = cur.fetchone()

                if (
                    verification["status"]
                    in TERMINAL_RECOVERY_STATUSES
                ):
                    return {
                        **verification,
                        "healthy_now": (
                            verification["status"]
                            == "RECOVERED"
                        ),
                        "should_retry": False,
                        "reused": True,
                    }

                attempt_count = (
                    verification["attempt_count"]
                    + 1
                )

                if (
                    observation.telemetry_available
                    and observation.healthy
                ):
                    consecutive_healthy = (
                        verification[
                            "consecutive_healthy"
                        ]
                        + 1
                    )
                else:
                    consecutive_healthy = 0

                if not observation.telemetry_available:
                    if (
                        attempt_count
                        >= MAX_RECOVERY_ATTEMPTS
                    ):
                        new_status = "INCONCLUSIVE"
                    else:
                        new_status = "VERIFYING"

                elif (
                    consecutive_healthy
                    >= REQUIRED_HEALTHY_CHECKS
                ):
                    new_status = "RECOVERED"

                elif (
                    attempt_count
                    >= MAX_RECOVERY_ATTEMPTS
                ):
                    new_status = "NOT_RECOVERED"

                else:
                    new_status = "VERIFYING"

                evidence = (
                    verification["evidence"]
                    or {}
                )

                checks = list(
                    evidence.get(
                        "checks",
                        [],
                    )
                )

                checks.append(
                    {
                        "attempt":
                            attempt_count,
                        "checked_at":
                            checked_at.isoformat(),
                        "telemetry_available":
                            observation.telemetry_available,
                        "healthy":
                            observation.healthy,
                        "triggered":
                            observation.triggered,
                        "observed_value":
                            observation.observed_value,
                        "threshold":
                            observation.threshold,
                    }
                )

                updated_evidence = {
                    "rule_key":
                        observation.rule_key,
                    "service":
                        observation.service,
                    "max_attempts":
                        MAX_RECOVERY_ATTEMPTS,
                    "required_healthy_checks":
                        REQUIRED_HEALTHY_CHECKS,
                    "checks":
                        checks,
                }

                verified_at = (
                    checked_at
                    if new_status
                    in TERMINAL_RECOVERY_STATUSES
                    else None
                )

                cur.execute(
                    """
                    UPDATE recovery_verifications
                    SET
                        status = %s,
                        attempt_count = %s,
                        consecutive_healthy = %s,
                        last_observed_value = %s,
                        evidence = %s,
                        first_checked_at =
                            COALESCE(
                                first_checked_at,
                                %s
                            ),
                        last_checked_at = %s,
                        verified_at = %s
                    WHERE execution_id = %s
                    RETURNING *
                    """,
                    (
                        new_status,
                        attempt_count,
                        consecutive_healthy,
                        observation.observed_value,
                        Jsonb(updated_evidence),
                        checked_at,
                        checked_at,
                        verified_at,
                        execution_id,
                    ),
                )

                updated = cur.fetchone()

    except psycopg.Error as exc:
        raise RuntimeError(
            "Could not persist recovery verification."
        ) from exc

    if updated["status"] == "RECOVERED":
        _ensure_incident_resolved(
            context["fingerprint"]
        )

    return {
        **updated,
        "healthy_now":
            observation.healthy,
        "telemetry_available":
            observation.telemetry_available,
        "should_retry":
            updated["status"] == "VERIFYING",
        "max_attempts":
            MAX_RECOVERY_ATTEMPTS,
        "required_healthy_checks":
            REQUIRED_HEALTHY_CHECKS,
        "reused": False,
    }

def _ensure_incident_resolved(
    fingerprint: str,
) -> None:
    resolve_incident(
        fingerprint
    )
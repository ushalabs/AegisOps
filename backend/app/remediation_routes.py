
import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from app.db.database import get_connection
from app.remediation import REMEDIATION_CATALOG

from secrets import compare_digest
from typing import Literal

from fastapi import Header
from app.core.config import settings

router = APIRouter(
    prefix="/remediations",
    tags=["Remediation"],
)


class CreateProposalRequest(BaseModel):
    incident_id: int = Field(gt=0)
    investigation_id: int = Field(gt=0)
    action_key: str

    rationale: str = Field(min_length=15, max_length=2000)
    expected_outcome: str = Field(min_length=10, max_length=1000)


@router.post("/proposals", status_code=201)
def create_proposal(request: CreateProposalRequest):
    action = REMEDIATION_CATALOG.get(request.action_key)

    if action is None:
        raise HTTPException(
            status_code=422,
            detail="Action is not in the remediation catalog.",
        )

    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Lock the incident while validating and creating
                # its proposal.
                cur.execute(
                    """
                    SELECT id, service, status
                    FROM incidents
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (request.incident_id,),
                )
                incident = cur.fetchone()

                if incident is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Incident not found.",
                    )

                if incident["status"] != "OPEN":
                    raise HTTPException(
                        status_code=409,
                        detail="Only OPEN incidents can receive proposals.",
                    )

                # Never allow an action intended for a different service.
                if incident["service"] != action.target_service:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "message": "Action does not match incident service.",
                            "incident_service": incident["service"],
                            "action_target": action.target_service,
                        },
                    )

                # Verify that this investigation belongs to the incident.
                cur.execute(
                    """
                    SELECT id
                    FROM investigations
                    WHERE id = %s
                      AND incident_id = %s
                    """,
                    (
                        request.investigation_id,
                        request.incident_id,
                    ),
                )

                if cur.fetchone() is None:
                    raise HTTPException(
                        status_code=422,
                        detail="Investigation does not belong to this incident.",
                    )

                # Clear an expired pending proposal for this action
                # before attempting to create a new one.
                cur.execute(
                    """
                    UPDATE remediation_proposals
                    SET status = 'EXPIRED'
                    WHERE incident_id = %s
                      AND action_key = %s
                      AND status = 'PENDING'
                      AND expires_at <= NOW()
                    """,
                    (request.incident_id, action.key),
                )

                cur.execute(
                    """
                    INSERT INTO remediation_proposals (
                        incident_id,
                        investigation_id,
                        action_key,
                        target_service,
                        rationale,
                        expected_outcome,
                        risk_level
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (incident_id, action_key)
                        WHERE status = 'PENDING'
                    DO NOTHING
                    RETURNING
                        id,
                        incident_id,
                        investigation_id,
                        action_key,
                        target_service,
                        risk_level,
                        status,
                        created_at,
                        expires_at
                    """,
                    (
                        request.incident_id,
                        request.investigation_id,
                        action.key,
                        action.target_service,
                        request.rationale,
                        request.expected_outcome,
                        action.risk_level,
                    ),
                )

                proposal = cur.fetchone()

                if proposal is None:
                    raise HTTPException(
                        status_code=409,
                        detail="A pending proposal already exists for this action.",
                    )

                return proposal

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="Database operation failed.",
        )


@router.get("/proposals/{proposal_id}")
def get_proposal(proposal_id: int):
    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM remediation_proposals
                    WHERE id = %s
                    """,
                    (proposal_id,),
                )

                proposal = cur.fetchone()

                if proposal is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Proposal not found.",
                    )

                return proposal

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="Database operation failed.",
        )


@router.post("/from-investigation/{investigation_id}", status_code=201)
def propose_from_investigation(investigation_id: int):
    if investigation_id < 1:
        raise HTTPException(
            status_code=422,
            detail="Invalid investigation ID.",
        )

    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        inv.id AS investigation_id,
                        inv.incident_id,
                        inv.report,
                        i.service,
                        i.status
                    FROM investigations inv
                    JOIN incidents i
                        ON i.id = inv.incident_id
                    WHERE inv.id = %s
                    """,
                    (investigation_id,),
                )
                record = cur.fetchone()

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve investigation.",
        )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    if record["status"] != "OPEN":
        raise HTTPException(
            status_code=409,
            detail="The incident has already been resolved.",
        )

    # Only availability incidents receive automatic action
    # candidates at this stage. API problems require manual review.
    action_by_service = {
        "benchmark-redis": "restart_benchmark_redis",
        "benchmark-postgresql": "restart_benchmark_postgresql",
    }

    expected_outcome_by_service = {
        "benchmark-redis":
            "Attempt to restore Redis availability. "
            "Recovery must be verified separately.",

        "benchmark-postgresql":
            "Attempt to restore PostgreSQL availability. "
            "Recovery must be verified separately.",
    }

    service = record["service"]
    action_key = action_by_service.get(service)

    if action_key is None:
        raise HTTPException(
            status_code=422,
            detail="This service requires manual action selection.",
        )

    report = record["report"] or {}
    summary = report.get("summary", "")

    if not isinstance(summary, str) or len(summary.strip()) < 15:
        raise HTTPException(
            status_code=422,
            detail="Investigation has no usable summary.",
        )

    return create_proposal(
        CreateProposalRequest(
            incident_id=record["incident_id"],
            investigation_id=investigation_id,
            action_key=action_key,
            rationale=summary.strip()[:2000],
            expected_outcome=expected_outcome_by_service[service],
        )
    )


class ReviewProposalRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    reviewer: str = Field(min_length=3, max_length=100)
    note: str = Field(min_length=5, max_length=1000)


@router.post("/proposals/{proposal_id}/review")
def review_proposal(
    proposal_id: int,
    request: ReviewProposalRequest,
    review_key: str | None = Header(
        default=None,
        alias="X-AegisOps-Review-Key",
    ),
):
    expected_key = settings.remediation_review_key

    if (
        not expected_key
        or not review_key
        or not compare_digest(review_key, expected_key)
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid remediation review credentials.",
        )

    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT incident_id
                    FROM remediation_proposals
                    WHERE id = %s
                    """,
                    (proposal_id,),
                )
                reference = cur.fetchone()

                if reference is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Proposal not found.",
                    )

                # Lock the incident first, then the proposal.
                # This keeps the lock order consistent with creation.
                cur.execute(
                    """
                    SELECT id, status
                    FROM incidents
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (reference["incident_id"],),
                )
                incident = cur.fetchone()

                cur.execute(
                    """
                    SELECT
                        id,
                        status,
                        expires_at > NOW() AS not_expired
                    FROM remediation_proposals
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (proposal_id,),
                )
                proposal = cur.fetchone()

                if proposal["status"] != "PENDING":
                    raise HTTPException(
                        status_code=409,
                        detail="Proposal has already been reviewed or closed.",
                    )

                if not proposal["not_expired"]:
                    raise HTTPException(
                        status_code=409,
                        detail="Proposal has expired.",
                    )

                if (
                    request.decision == "APPROVED"
                    and incident["status"] != "OPEN"
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Cannot approve remediation for a resolved incident.",
                    )

                cur.execute(
                    """
                    UPDATE remediation_proposals
                    SET
                        status = %s,
                        reviewed_by = %s,
                        reviewed_at = NOW(),
                        review_note = %s
                    WHERE id = %s
                    RETURNING
                        id,
                        incident_id,
                        action_key,
                        target_service,
                        risk_level,
                        status,
                        reviewed_by,
                        reviewed_at,
                        review_note
                    """,
                    (
                        request.decision,
                        request.reviewer,
                        request.note,
                        proposal_id,
                    ),
                )

                return cur.fetchone()

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="Could not save the review decision.",
        )

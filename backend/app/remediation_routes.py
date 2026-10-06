import httpx
import psycopg

from datetime import datetime, timezone
from secrets import compare_digest
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from app.core.config import settings
from app.db.database import get_connection
from app.remediation import (
    REMEDIATION_CATALOG,
    execute_remediation_action,
)


router = APIRouter(
    prefix="/remediations",
    tags=["Remediation"],
)


class CreateProposalRequest(BaseModel):
    incident_id: int = Field(gt=0)
    investigation_id: int = Field(gt=0)
    action_key: str

    rationale: str = Field(
        min_length=15,
        max_length=2000,
    )
    expected_outcome: str = Field(
        min_length=10,
        max_length=1000,
    )


@router.post("/proposals", status_code=201)
def create_proposal(
    request: CreateProposalRequest,
):
    action = REMEDIATION_CATALOG.get(
        request.action_key
    )

    if action is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "Action is not in the remediation catalog."
            ),
        )

    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

                # Lock the incident while validating and
                # creating its proposal.
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
                        detail=(
                            "Only OPEN incidents can "
                            "receive proposals."
                        ),
                    )

                # Never allow an action intended for
                # a different service.
                if (
                    incident["service"]
                    != action.target_service
                ):
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "message": (
                                "Action does not match "
                                "incident service."
                            ),
                            "incident_service":
                                incident["service"],
                            "action_target":
                                action.target_service,
                        },
                    )

                # Verify that this investigation belongs
                # to the incident.
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
                        detail=(
                            "Investigation does not belong "
                            "to this incident."
                        ),
                    )

                # Clear an expired pending proposal for
                # this action before attempting to create
                # a new one.
                cur.execute(
                    """
                    UPDATE remediation_proposals
                    SET status = 'EXPIRED'
                    WHERE incident_id = %s
                      AND action_key = %s
                      AND status = 'PENDING'
                      AND expires_at <= NOW()
                    """,
                    (
                        request.incident_id,
                        action.key,
                    ),
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
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    ON CONFLICT (
                        incident_id,
                        action_key
                    )
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
                        detail=(
                            "A pending proposal already "
                            "exists for this action."
                        ),
                    )

                return proposal

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="Database operation failed.",
        )


@router.get("/proposals")
def list_proposals(
    status: Literal[
        "PENDING",
        "APPROVED",
        "REJECTED",
        "EXPIRED",
        "CANCELLED",
    ] | None = None,
):
    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

                if status == "PENDING":
                    cur.execute(
                        """
                        SELECT
                            rp.id,
                            rp.incident_id,
                            rp.investigation_id,
                            rp.action_key,
                            rp.target_service,
                            rp.rationale,
                            rp.expected_outcome,
                            rp.risk_level,
                            rp.status,
                            rp.created_at,
                            rp.expires_at,
                            rp.reviewed_by,
                            rp.reviewed_at,
                            rp.review_note,
                            i.title
                                AS incident_title,
                            i.severity
                                AS incident_severity,
                            i.status
                                AS incident_status
                        FROM remediation_proposals AS rp
                        JOIN incidents AS i
                            ON i.id = rp.incident_id
                        WHERE rp.status = 'PENDING'
                          AND rp.expires_at > NOW()
                        ORDER BY rp.created_at DESC
                        """
                    )

                elif status is not None:
                    cur.execute(
                        """
                        SELECT
                            rp.id,
                            rp.incident_id,
                            rp.investigation_id,
                            rp.action_key,
                            rp.target_service,
                            rp.rationale,
                            rp.expected_outcome,
                            rp.risk_level,
                            rp.status,
                            rp.created_at,
                            rp.expires_at,
                            rp.reviewed_by,
                            rp.reviewed_at,
                            rp.review_note,
                            i.title
                                AS incident_title,
                            i.severity
                                AS incident_severity,
                            i.status
                                AS incident_status
                        FROM remediation_proposals AS rp
                        JOIN incidents AS i
                            ON i.id = rp.incident_id
                        WHERE rp.status = %s
                        ORDER BY rp.created_at DESC
                        """,
                        (status,),
                    )

                else:
                    cur.execute(
                        """
                        SELECT
                            rp.id,
                            rp.incident_id,
                            rp.investigation_id,
                            rp.action_key,
                            rp.target_service,
                            rp.rationale,
                            rp.expected_outcome,
                            rp.risk_level,
                            rp.status,
                            rp.created_at,
                            rp.expires_at,
                            rp.reviewed_by,
                            rp.reviewed_at,
                            rp.review_note,
                            i.title
                                AS incident_title,
                            i.severity
                                AS incident_severity,
                            i.status
                                AS incident_status
                        FROM remediation_proposals AS rp
                        JOIN incidents AS i
                            ON i.id = rp.incident_id
                        ORDER BY rp.created_at DESC
                        """
                    )

                return cur.fetchall()

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not retrieve remediation proposals."
            ),
        )


@router.get("/proposals/{proposal_id}")
def get_proposal(
    proposal_id: int,
):
    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:
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


@router.post(
    "/from-investigation/{investigation_id}",
    status_code=201,
)
def propose_from_investigation(
    investigation_id: int,
):
    if investigation_id < 1:
        raise HTTPException(
            status_code=422,
            detail="Invalid investigation ID.",
        )

    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

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
            detail=(
                "Could not retrieve investigation."
            ),
        )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    if record["status"] != "OPEN":
        raise HTTPException(
            status_code=409,
            detail=(
                "The incident has already been resolved."
            ),
        )

    # Only availability incidents receive automatic
    # action candidates at this stage.
    # API problems require manual action selection.
    action_by_service = {
        "benchmark-redis":
            "restart_benchmark_redis",

        "benchmark-postgresql":
            "restart_benchmark_postgresql",
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

    action_key = action_by_service.get(
        service
    )

    if action_key is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "This service requires manual "
                "action selection."
            ),
        )

    report = record["report"] or {}

    summary = report.get(
        "summary",
        "",
    )

    if (
        not isinstance(summary, str)
        or len(summary.strip()) < 15
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Investigation has no usable summary."
            ),
        )

    return create_proposal(
        CreateProposalRequest(
            incident_id=record["incident_id"],
            investigation_id=investigation_id,
            action_key=action_key,
            rationale=summary.strip()[:2000],
            expected_outcome=(
                expected_outcome_by_service[
                    service
                ]
            ),
        )
    )


class ReviewProposalRequest(BaseModel):
    decision: Literal[
        "APPROVED",
        "REJECTED",
    ]

    reviewer: str = Field(
        min_length=3,
        max_length=100,
    )

    note: str = Field(
        min_length=5,
        max_length=1000,
    )


class RegisterCallbackRequest(BaseModel):
    resume_url: str = Field(
        min_length=20,
        max_length=3000,
    )


@router.post(
    "/proposals/{proposal_id}/callback"
)
def register_remediation_callback(
    proposal_id: int,
    request: RegisterCallbackRequest,
    execution_key: str | None = Header(
        default=None,
        alias="X-AegisOps-Execution-Key",
    ),
):
    expected_key = (
        settings.remediation_execution_key
    )

    if (
        not expected_key
        or not execution_key
        or not compare_digest(
            execution_key,
            expected_key,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Invalid remediation callback "
                "credentials."
            ),
        )

    parsed_url = urlparse(
        request.resume_url
    )

    if (
        parsed_url.scheme not in {
            "http",
            "https",
        }
        or parsed_url.hostname not in {
            "127.0.0.1",
            "localhost",
        }
        or parsed_url.port != 5678
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Callback URL is not an "
                "allowed n8n URL."
            ),
        )

    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        status,
                        expires_at
                    FROM remediation_proposals
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (proposal_id,),
                )

                proposal = cur.fetchone()

                if proposal is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            "Remediation proposal "
                            "not found."
                        ),
                    )

                if (
                    proposal["status"]
                    != "PENDING"
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Only PENDING proposals "
                            "can register an approval "
                            "callback."
                        ),
                    )

                if (
                    proposal["expires_at"]
                    <= datetime.now(
                        timezone.utc
                    )
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "The remediation proposal "
                            "has expired."
                        ),
                    )

                cur.execute(
                    """
                    INSERT INTO remediation_callbacks (
                        proposal_id,
                        resume_url
                    )
                    VALUES (%s, %s)
                    ON CONFLICT (proposal_id)
                    DO UPDATE SET
                        resume_url =
                            EXCLUDED.resume_url,
                        registered_at = NOW(),
                        resumed_at = NULL
                    RETURNING
                        proposal_id,
                        registered_at
                    """,
                    (
                        proposal_id,
                        request.resume_url,
                    ),
                )

                callback = cur.fetchone()

                return {
                    "proposal_id":
                        callback[
                            "proposal_id"
                        ],
                    "callback_registered":
                        True,
                    "registered_at":
                        callback[
                            "registered_at"
                        ],
                }

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not register "
                "remediation callback."
            ),
        )


@router.post(
    "/proposals/{proposal_id}/review"
)
def review_proposal(
    proposal_id: int,
    request: ReviewProposalRequest,
    review_key: str | None = Header(
        default=None,
        alias="X-AegisOps-Review-Key",
    ),
):
    expected_key = (
        settings.remediation_review_key
    )

    if (
        not expected_key
        or not review_key
        or not compare_digest(
            review_key,
            expected_key,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Invalid remediation review "
                "credentials."
            ),
        )

    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

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
                        detail=(
                            "Proposal not found."
                        ),
                    )

                # Lock the incident first, then
                # the proposal.
                cur.execute(
                    """
                    SELECT id, status
                    FROM incidents
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (
                        reference[
                            "incident_id"
                        ],
                    ),
                )

                incident = cur.fetchone()

                cur.execute(
                    """
                    SELECT
                        id,
                        status,
                        expires_at > NOW()
                            AS not_expired
                    FROM remediation_proposals
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (proposal_id,),
                )

                proposal = cur.fetchone()

                if (
                    proposal["status"]
                    != "PENDING"
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Proposal has already "
                            "been reviewed or closed."
                        ),
                    )

                if not proposal[
                    "not_expired"
                ]:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Proposal has expired."
                        ),
                    )

                if (
                    request.decision
                    == "APPROVED"
                    and incident["status"]
                    != "OPEN"
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Cannot approve "
                            "remediation for a "
                            "resolved incident."
                        ),
                    )

                cur.execute(
                    """
                    SELECT
                        resume_url,
                        resumed_at
                    FROM remediation_callbacks
                    WHERE proposal_id = %s
                    """,
                    (proposal_id,),
                )

                callback = cur.fetchone()

                if callback is None:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "No orchestration "
                            "callback is registered "
                            "for this proposal."
                        ),
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

                reviewed_proposal = (
                    cur.fetchone()
                )

                resume_url = callback[
                    "resume_url"
                ]

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not save the "
                "review decision."
            ),
        )

    # The database transaction has committed
    # before n8n is resumed. This ensures that
    # n8n sees the final review state when it
    # fetches the proposal again.
    try:
        response = httpx.post(
            resume_url,
            json={
                "proposal_id":
                    proposal_id,
                "status":
                    request.decision,
            },
            timeout=5.0,
        )

        response.raise_for_status()

    except httpx.HTTPError:
        return {
            **reviewed_proposal,
            "workflow_resumed":
                False,
            "callback_audit_updated":
                False,
        }

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE remediation_callbacks
                    SET resumed_at = NOW()
                    WHERE proposal_id = %s
                      AND resumed_at IS NULL
                    """,
                    (proposal_id,),
                )

    except psycopg.Error:
        return {
            **reviewed_proposal,
            "workflow_resumed":
                True,
            "callback_audit_updated":
                False,
        }

    return {
        **reviewed_proposal,
        "workflow_resumed":
            True,
        "callback_audit_updated":
            True,
    }


@router.post(
    "/proposals/{proposal_id}/execute"
)
def execute_approved_proposal(
    proposal_id: int,
    execution_key: str | None = Header(
        default=None,
        alias="X-AegisOps-Execution-Key",
    ),
):
    expected_key = (
        settings.remediation_execution_key
    )

    if (
        not expected_key
        or not execution_key
        or not compare_digest(
            execution_key,
            expected_key,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Invalid remediation execution "
                "credentials."
            ),
        )

    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

                # Find the associated incident first
                # so we preserve the same lock order
                # used elsewhere.
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
                        detail=(
                            "Remediation proposal "
                            "not found."
                        ),
                    )

                cur.execute(
                    """
                    SELECT id, status
                    FROM incidents
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (
                        reference[
                            "incident_id"
                        ],
                    ),
                )

                incident = cur.fetchone()

                cur.execute(
                    """
                    SELECT
                        id,
                        incident_id,
                        action_key,
                        target_service,
                        status,
                        expires_at
                    FROM remediation_proposals
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (proposal_id,),
                )

                proposal = cur.fetchone()

                # IMPORTANT:
                # Check idempotency before checking
                # current proposal/incident state.
                #
                # If this proposal has already been
                # executed, this request must simply
                # return the existing execution.
                # It must never run the remediation
                # action a second time.
                cur.execute(
                    """
                    SELECT *
                    FROM remediation_executions
                    WHERE proposal_id = %s
                    """,
                    (proposal_id,),
                )

                existing_execution = (
                    cur.fetchone()
                )

                if (
                    existing_execution
                    is not None
                ):
                    return {
                        **existing_execution,
                        "reused": True,
                    }

                # The validations below apply only
                # when this would be a NEW execution.
                if (
                    proposal["status"]
                    != "APPROVED"
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Only APPROVED "
                            "proposals can be "
                            "executed."
                        ),
                    )

                if (
                    proposal["expires_at"]
                    <= datetime.now(
                        timezone.utc
                    )
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "The remediation "
                            "authorization has "
                            "expired."
                        ),
                    )

                if (
                    incident["status"]
                    != "OPEN"
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Cannot execute "
                            "remediation for a "
                            "resolved incident."
                        ),
                    )

                action = (
                    REMEDIATION_CATALOG.get(
                        proposal[
                            "action_key"
                        ]
                    )
                )

                if action is None:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            "Proposal references "
                            "an unsupported action."
                        ),
                    )

                if (
                    action.target_service
                    != proposal[
                        "target_service"
                    ]
                ):
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            "Proposal target "
                            "does not match "
                            "remediation catalog."
                        ),
                    )

                # The unique proposal_id constraint
                # in remediation_executions prevents
                # duplicate execution records.
                cur.execute(
                    """
                    INSERT INTO
                        remediation_executions (
                            proposal_id,
                            incident_id,
                            action_key,
                            target_service,
                            status
                        )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        'RUNNING'
                    )
                    RETURNING id
                    """,
                    (
                        proposal["id"],
                        proposal[
                            "incident_id"
                        ],
                        proposal[
                            "action_key"
                        ],
                        proposal[
                            "target_service"
                        ],
                    ),
                )

                execution_id = (
                    cur.fetchone()["id"]
                )

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not prepare "
                "remediation execution."
            ),
        )

    # Docker is intentionally executed outside
    # the DB transaction.
    result = execute_remediation_action(
        proposal["action_key"]
    )

    final_status = (
        "SUCCEEDED"
        if result["success"]
        else "FAILED"
    )

    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

                cur.execute(
                    """
                    UPDATE remediation_executions
                    SET
                        status = %s,
                        finished_at = NOW(),
                        exit_code = %s,
                        output = %s,
                        error = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (
                        final_status,
                        result["exit_code"],
                        result[
                            "stdout"
                        ][:4000],
                        result[
                            "stderr"
                        ][:4000],
                        execution_id,
                    ),
                )

                execution = cur.fetchone()

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Remediation command ran, "
                "but its execution record "
                "could not be finalized."
            ),
        )

    return {
        **execution,
        "reused": False,
    }
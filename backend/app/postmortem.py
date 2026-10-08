from datetime import datetime

from psycopg.rows import dict_row

from app.db.database import get_connection
from psycopg.types.json import Jsonb

from app.postmortem_schemas import (
    IncidentPostmortemReport,
)
from pgvector.psycopg import register_vector

from app.knowledge.embeddings import (
    EMBEDDING_MODEL,
    embed_texts,
)

from app.knowledge.embeddings import (
    EMBEDDING_MODEL,
    embed_texts,
    embed_query,
)

def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()


def build_incident_timeline(
    incident_id: int,
) -> dict:
    with get_connection() as conn:
        with conn.cursor(
            row_factory=dict_row
        ) as cur:

            # -------------------------------------------------
            # Incident
            # -------------------------------------------------
            cur.execute(
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
                """,
                (incident_id,),
            )

            incident = cur.fetchone()

            if incident is None:
                raise ValueError(
                    "Incident not found."
                )

            # -------------------------------------------------
            # Investigations
            # -------------------------------------------------
            cur.execute(
                """
                SELECT
                    id,
                    model,
                    evidence_collected_at,
                    evidence,
                    report,
                    created_at
                FROM investigations
                WHERE incident_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (incident_id,),
            )

            investigations = cur.fetchall()

            # -------------------------------------------------
            # Remediation proposals
            # -------------------------------------------------
            cur.execute(
                """
                SELECT
                    id,
                    investigation_id,
                    action_key,
                    target_service,
                    rationale,
                    expected_outcome,
                    risk_level,
                    status,
                    created_at,
                    expires_at,
                    reviewed_by,
                    reviewed_at,
                    review_note
                FROM remediation_proposals
                WHERE incident_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (incident_id,),
            )

            proposals = cur.fetchall()

            # -------------------------------------------------
            # Remediation executions
            # -------------------------------------------------
            cur.execute(
                """
                SELECT
                    id,
                    proposal_id,
                    action_key,
                    target_service,
                    status,
                    started_at,
                    finished_at,
                    exit_code,
                    output,
                    error
                FROM remediation_executions
                WHERE incident_id = %s
                ORDER BY started_at ASC, id ASC
                """,
                (incident_id,),
            )

            executions = cur.fetchall()

            # -------------------------------------------------
            # Recovery verification
            # -------------------------------------------------
            cur.execute(
                """
                SELECT
                    id,
                    execution_id,
                    rule_key,
                    status,
                    attempt_count,
                    consecutive_healthy,
                    last_observed_value,
                    evidence,
                    created_at,
                    first_checked_at,
                    last_checked_at,
                    verified_at
                FROM recovery_verifications
                WHERE incident_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (incident_id,),
            )

            recoveries = cur.fetchall()

    timeline: list[dict] = []

    # ---------------------------------------------------------
    # Incident created
    # ---------------------------------------------------------
    timeline.append(
        {
            "event_type": "INCIDENT_CREATED",
            "timestamp": _iso(
                incident[
                    "first_detected_at"
                ]
            ),
            "details": {
                "rule_key":
                    incident["rule_key"],
                "service":
                    incident["service"],
                "severity":
                    incident["severity"],
                "trigger_value":
                    incident["trigger_value"],
                "threshold":
                    incident["threshold"],
            },
        }
    )

    # ---------------------------------------------------------
    # Investigations
    # ---------------------------------------------------------
    for investigation in investigations:
        report = (
            investigation["report"]
            or {}
        )

        timeline.append(
            {
                "event_type":
                    "INVESTIGATION_COMPLETED",
                "timestamp": _iso(
                    investigation[
                        "created_at"
                    ]
                ),
                "details": {
                    "investigation_id":
                        investigation["id"],
                    "model":
                        investigation["model"],
                    "summary":
                        report.get("summary"),
                    "confidence":
                        report.get(
                            "confidence"
                        ),
                },
            }
        )

    # ---------------------------------------------------------
    # Proposals + reviews
    # ---------------------------------------------------------
    for proposal in proposals:
        timeline.append(
            {
                "event_type":
                    "REMEDIATION_PROPOSED",
                "timestamp": _iso(
                    proposal["created_at"]
                ),
                "details": {
                    "proposal_id":
                        proposal["id"],
                    "investigation_id":
                        proposal[
                            "investigation_id"
                        ],
                    "action_key":
                        proposal["action_key"],
                    "target_service":
                        proposal[
                            "target_service"
                        ],
                    "risk_level":
                        proposal["risk_level"],
                    "rationale":
                        proposal["rationale"],
                    "expected_outcome":
                        proposal[
                            "expected_outcome"
                        ],
                },
            }
        )

        if proposal["reviewed_at"]:
            event_type = (
                "REMEDIATION_APPROVED"
                if proposal["status"]
                == "APPROVED"
                else "REMEDIATION_REVIEWED"
            )

            timeline.append(
                {
                    "event_type":
                        event_type,
                    "timestamp": _iso(
                        proposal[
                            "reviewed_at"
                        ]
                    ),
                    "details": {
                        "proposal_id":
                            proposal["id"],
                        "decision":
                            proposal["status"],
                        "reviewed_by":
                            proposal[
                                "reviewed_by"
                            ],
                        "review_note":
                            proposal[
                                "review_note"
                            ],
                    },
                }
            )

    # ---------------------------------------------------------
    # Executions
    # ---------------------------------------------------------
    for execution in executions:
        timeline.append(
            {
                "event_type":
                    "REMEDIATION_EXECUTION_STARTED",
                "timestamp": _iso(
                    execution["started_at"]
                ),
                "details": {
                    "execution_id":
                        execution["id"],
                    "proposal_id":
                        execution[
                            "proposal_id"
                        ],
                    "action_key":
                        execution[
                            "action_key"
                        ],
                    "target_service":
                        execution[
                            "target_service"
                        ],
                },
            }
        )

        if execution["finished_at"]:
            timeline.append(
                {
                    "event_type": (
                        "REMEDIATION_SUCCEEDED"
                        if execution[
                            "status"
                        ]
                        == "SUCCEEDED"
                        else
                        "REMEDIATION_FAILED"
                    ),
                    "timestamp": _iso(
                        execution[
                            "finished_at"
                        ]
                    ),
                    "details": {
                        "execution_id":
                            execution["id"],
                        "status":
                            execution["status"],
                        "exit_code":
                            execution[
                                "exit_code"
                            ],
                    },
                }
            )

    # ---------------------------------------------------------
    # Recovery verification
    # ---------------------------------------------------------
    for recovery in recoveries:
        if recovery["first_checked_at"]:
            timeline.append(
                {
                    "event_type":
                        "RECOVERY_VERIFICATION_STARTED",
                    "timestamp": _iso(
                        recovery[
                            "first_checked_at"
                        ]
                    ),
                    "details": {
                        "verification_id":
                            recovery["id"],
                        "execution_id":
                            recovery[
                                "execution_id"
                            ],
                        "rule_key":
                            recovery["rule_key"],
                    },
                }
            )

        if recovery["verified_at"]:
            if (
                recovery["status"]
                == "RECOVERED"
            ):
                event_type = (
                    "RECOVERY_CONFIRMED"
                )
            elif (
                recovery["status"]
                == "NOT_RECOVERED"
            ):
                event_type = (
                    "RECOVERY_NOT_CONFIRMED"
                )
            else:
                event_type = (
                    "RECOVERY_INCONCLUSIVE"
                )

            timeline.append(
                {
                    "event_type":
                        event_type,
                    "timestamp": _iso(
                        recovery[
                            "verified_at"
                        ]
                    ),
                    "details": {
                        "verification_id":
                            recovery["id"],
                        "execution_id":
                            recovery[
                                "execution_id"
                            ],
                        "status":
                            recovery["status"],
                        "attempt_count":
                            recovery[
                                "attempt_count"
                            ],
                        "consecutive_healthy":
                            recovery[
                                "consecutive_healthy"
                            ],
                        "last_observed_value":
                            recovery[
                                "last_observed_value"
                            ],
                    },
                }
            )

    # ---------------------------------------------------------
    # Incident resolved
    # ---------------------------------------------------------
    if incident["resolved_at"]:
        timeline.append(
            {
                "event_type":
                    "INCIDENT_RESOLVED",
                "timestamp": _iso(
                    incident["resolved_at"]
                ),
                "details": {
                    "final_status":
                        incident["status"],
                },
            }
        )

    # Guarantee deterministic chronological order.
    timeline.sort(
        key=lambda event: (
            event["timestamp"] or "",
            event["event_type"],
        )
    )

    return {
        "incident": {
            "id":
                incident["id"],
            "fingerprint":
                incident["fingerprint"],
            "rule_key":
                incident["rule_key"],
            "title":
                incident["title"],
            "service":
                incident["service"],
            "severity":
                incident["severity"],
            "status":
                incident["status"],
            "trigger_value":
                incident["trigger_value"],
            "threshold":
                incident["threshold"],
            "first_detected_at":
                _iso(
                    incident[
                        "first_detected_at"
                    ]
                ),
            "resolved_at":
                _iso(
                    incident[
                        "resolved_at"
                    ]
                ),
        },

        "timeline": timeline,

        "investigations": [
            {
                **dict(record),
                "evidence_collected_at":
                    _iso(
                        record[
                            "evidence_collected_at"
                        ]
                    ),
                "created_at":
                    _iso(
                        record["created_at"]
                    ),
            }
            for record in investigations
        ],

        "remediation_proposals": [
            {
                **dict(record),
                "created_at":
                    _iso(
                        record["created_at"]
                    ),
                "expires_at":
                    _iso(
                        record["expires_at"]
                    ),
                "reviewed_at":
                    _iso(
                        record["reviewed_at"]
                    ),
            }
            for record in proposals
        ],

        "remediation_executions": [
            {
                **dict(record),
                "started_at":
                    _iso(
                        record["started_at"]
                    ),
                "finished_at":
                    _iso(
                        record["finished_at"]
                    ),
            }
            for record in executions
        ],

        "recovery_verifications": [
            {
                **dict(record),
                "created_at":
                    _iso(
                        record["created_at"]
                    ),
                "first_checked_at":
                    _iso(
                        record[
                            "first_checked_at"
                        ]
                    ),
                "last_checked_at":
                    _iso(
                        record[
                            "last_checked_at"
                        ]
                    ),
                "verified_at":
                    _iso(
                        record["verified_at"]
                    ),
            }
            for record in recoveries
        ],
    }

def save_incident_postmortem(
    incident_id: int,
    timeline: list[dict],
    report: IncidentPostmortemReport,
    model: str,
) -> dict:
    with get_connection() as conn:
        with conn.cursor(
            row_factory=dict_row
        ) as cur:

            cur.execute(
                """
                INSERT INTO incident_postmortems (
                    incident_id,
                    timeline,
                    summary,
                    root_cause,
                    impact,
                    what_went_well,
                    what_went_wrong,
                    lessons_learned,
                    preventive_actions,
                    model
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )

                ON CONFLICT (incident_id)
                DO UPDATE SET
                    timeline =
                        EXCLUDED.timeline,
                    summary =
                        EXCLUDED.summary,
                    root_cause =
                        EXCLUDED.root_cause,
                    impact =
                        EXCLUDED.impact,
                    what_went_well =
                        EXCLUDED.what_went_well,
                    what_went_wrong =
                        EXCLUDED.what_went_wrong,
                    lessons_learned =
                        EXCLUDED.lessons_learned,
                    preventive_actions =
                        EXCLUDED.preventive_actions,
                    model =
                        EXCLUDED.model,
                    updated_at =
                        NOW()

                RETURNING
                    id,
                    incident_id,
                    summary,
                    root_cause,
                    impact,
                    model,
                    created_at,
                    updated_at
                """,
                (
                    incident_id,
                    Jsonb(timeline),
                    report.summary,
                    report.probable_root_cause,
                    report.impact,
                    Jsonb(
                        report.what_went_well
                    ),

                    # Schema calls this
                    # what_could_be_improved.
                    # Database column is
                    # what_went_wrong.
                    Jsonb(
                        report.what_could_be_improved
                    ),

                    Jsonb(
                        report.lessons_learned
                    ),

                    Jsonb(
                        [
                            action.model_dump(
                                mode="json"
                            )
                            for action
                            in report.preventive_actions
                        ]
                    ),

                    model,
                ),
            )

            return cur.fetchone()


def build_incident_memory_text(
    incident: dict,
    report: IncidentPostmortemReport,
) -> str:
    preventive_actions = "\n".join(
        f"- {action.action}"
        for action in report.preventive_actions
    )

    lessons = "\n".join(
        f"- {lesson}"
        for lesson in report.lessons_learned
    )

    return f"""
Incident: {incident["title"]}
Service: {incident["service"]}
Rule: {incident["rule_key"]}
Severity: {incident["severity"]}

Summary:
{report.summary}

Probable Root Cause:
{report.probable_root_cause}

Root Cause Confidence:
{report.root_cause_confidence}

Impact:
{report.impact}

Lessons Learned:
{lessons or "- None recorded"}

Preventive Actions:
{preventive_actions or "- None recorded"}
""".strip()

def save_incident_memory(
    incident_id: int,
    postmortem_id: int,
    memory_text: str,
    metadata: dict | None = None,
) -> dict:
    embedding = embed_texts(
        [memory_text]
    )[0]

    with get_connection() as conn:
        register_vector(conn)

        with conn.cursor(
            row_factory=dict_row
        ) as cur:

            cur.execute(
                """
                INSERT INTO incident_memories (
                    incident_id,
                    postmortem_id,
                    memory_text,
                    embedding_model,
                    embedding,
                    metadata
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )

                ON CONFLICT (incident_id)
                DO UPDATE SET
                    postmortem_id =
                        EXCLUDED.postmortem_id,
                    memory_text =
                        EXCLUDED.memory_text,
                    embedding_model =
                        EXCLUDED.embedding_model,
                    embedding =
                        EXCLUDED.embedding,
                    metadata =
                        EXCLUDED.metadata,
                    updated_at =
                        NOW()

                RETURNING
                    id,
                    incident_id,
                    postmortem_id,
                    memory_text,
                    embedding_model,
                    created_at,
                    updated_at
                """,
                (
                    incident_id,
                    postmortem_id,
                    memory_text,
                    EMBEDDING_MODEL,
                    embedding,
                    Jsonb(
                        metadata or {}
                    ),
                ),
            )

            return cur.fetchone()

def search_incident_memories(
    query: str,
    limit: int = 5,
    exclude_incident_id: int | None = None,
) -> list[dict]:
    if not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    if not 1 <= limit <= 10:
        raise ValueError(
            "Limit must be between 1 and 10."
        )

    query_embedding = embed_query(
        query
    )

    with get_connection() as conn:
        register_vector(conn)

        with conn.cursor(
            row_factory=dict_row
        ) as cur:

            if exclude_incident_id is None:
                cur.execute(
                    """
                    SELECT
                        im.id AS memory_id,
                        im.incident_id,
                        im.postmortem_id,
                        im.memory_text,
                        im.metadata,
                        i.title,
                        i.service,
                        i.rule_key,
                        i.severity,
                        1 - (
                            im.embedding <=> %s
                        ) AS similarity
                    FROM incident_memories AS im
                    JOIN incidents AS i
                        ON i.id = im.incident_id
                    WHERE
                        im.embedding_model = %s
                    ORDER BY
                        im.embedding <=> %s
                    LIMIT %s
                    """,
                    (
                        query_embedding,
                        EMBEDDING_MODEL,
                        query_embedding,
                        limit,
                    ),
                )

            else:
                cur.execute(
                    """
                    SELECT
                        im.id AS memory_id,
                        im.incident_id,
                        im.postmortem_id,
                        im.memory_text,
                        im.metadata,
                        i.title,
                        i.service,
                        i.rule_key,
                        i.severity,
                        1 - (
                            im.embedding <=> %s
                        ) AS similarity
                    FROM incident_memories AS im
                    JOIN incidents AS i
                        ON i.id = im.incident_id
                    WHERE
                        im.embedding_model = %s
                        AND im.incident_id != %s
                    ORDER BY
                        im.embedding <=> %s
                    LIMIT %s
                    """,
                    (
                        query_embedding,
                        EMBEDDING_MODEL,
                        exclude_incident_id,
                        query_embedding,
                        limit,
                    ),
                )

            rows = cur.fetchall()

    return [
        {
            **dict(row),
            "similarity":
                float(row["similarity"]),
        }
        for row in rows
    ]

def get_postmortem_by_incident(
    incident_id: int,
) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM incident_postmortems
                WHERE incident_id = %s
                """,
                (incident_id,),
            )

            return cur.fetchone()

def get_incident_memory_by_incident(
    incident_id: int,
) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(
            row_factory=dict_row
        ) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    incident_id,
                    postmortem_id,
                    memory_text,
                    embedding_model,
                    metadata,
                    created_at,
                    updated_at
                FROM incident_memories
                WHERE incident_id = %s
                """,
                (incident_id,),
            )

            return cur.fetchone()
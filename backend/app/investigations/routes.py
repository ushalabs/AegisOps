import logging
import time

from uuid import UUID

import psycopg

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from langgraph.checkpoint.postgres import (
    PostgresSaver,
)

from psycopg.conninfo import (
    make_conninfo,
)

from app.core.config import settings

from app.investigations.agent import (
    builder,
)

from app.investigations.evidence import (
    collect_incident_evidence,
)

from app.investigations.gemini_client import (
    investigate_with_gemini,
)

from app.investigations.repository import (
    get_investigation_by_id,
    list_investigations_for_incident,
    save_investigation,
)

from app.knowledge.repository import (
    search_knowledge_chunks,
)

from app.knowledge.reranking import (
    build_rag_context,
)

from app.observability.metrics import (
    INVESTIGATION_DURATION,
    INVESTIGATION_RUNS,
)

from app.postmortem import (
    search_incident_memories,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/investigations",
    tags=["investigations"],
)


def _invoke_graph_with_metrics(
    graph,
    graph_input,
    config: dict,
):
    started_at = (
        time.perf_counter()
    )

    try:
        result = graph.invoke(
            graph_input,
            config=config,
        )

    except Exception:
        duration = (
            time.perf_counter()
            - started_at
        )

        INVESTIGATION_RUNS.labels(
            outcome="ERROR",
        ).inc()

        INVESTIGATION_DURATION.labels(
            outcome="ERROR",
        ).observe(
            duration
        )

        raise

    duration = (
        time.perf_counter()
        - started_at
    )

    outcome = (
        result.get(
            "status"
        )
        or "UNKNOWN"
    )

    INVESTIGATION_RUNS.labels(
        outcome=str(
            outcome
        ),
    ).inc()

    INVESTIGATION_DURATION.labels(
        outcome=str(
            outcome
        ),
    ).observe(
        duration
    )

    return result


@router.post(
    "/{incident_id}/run"
)
def run_investigation(
    incident_id: int,
):
    try:
        evidence = (
            collect_incident_evidence(
                incident_id
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Incident database "
                "unavailable"
            ),
        ) from exc

    if (
        evidence[
            "incident"
        ][
            "status"
        ]
        != "OPEN"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Only OPEN incidents "
                "can be investigated"
            ),
        )

    incident = (
        evidence[
            "incident"
        ]
    )

    search_query = (
        f"{incident['title']}. "
        f"Affected service: "
        f"{incident['service']}. "
        "Find troubleshooting procedures, "
        "possible causes, diagnostic checks "
        "and recovery verification."
    )

    try:
        candidates = (
            search_knowledge_chunks(
                query=search_query,
                limit=10,
            )
        )

        rag_context = (
            build_rag_context(
                query=search_query,
                candidates=candidates,
                max_chunks=3,
                max_excerpt_chars=2400,
            )
        )

        historical_results = (
            search_incident_memories(
                query=search_query,
                limit=3,
                exclude_incident_id=(
                    incident_id
                ),
            )
        )

        evidence[
            "similar_historical_incidents"
        ] = [
            {
                "incident_id":
                    result[
                        "incident_id"
                    ],

                "title":
                    result[
                        "title"
                    ],

                "service":
                    result[
                        "service"
                    ],

                "rule_key":
                    result[
                        "rule_key"
                    ],

                "severity":
                    result[
                        "severity"
                    ],

                "similarity":
                    result[
                        "similarity"
                    ],

                "memory_text":
                    result[
                        "memory_text"
                    ][:2000],
            }
            for result
            in historical_results
        ]

    except psycopg.Error as exc:
        logger.exception(
            (
                "Knowledge retrieval "
                "failed for incident %s"
            ),
            incident_id,
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Knowledge database "
                "unavailable"
            ),
        ) from exc

    evidence[
        "retrieved_knowledge"
    ] = rag_context

    try:
        report = (
            investigate_with_gemini(
                evidence
            )
        )

    except Exception as exc:
        logger.exception(
            (
                "Gemini investigation "
                "failed for incident %s"
            ),
            incident_id,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Gemini investigation failed; "
                "check backend logs"
            ),
        ) from exc

    try:
        investigation_id = (
            save_investigation(
                incident_id=(
                    incident_id
                ),

                model=(
                    settings
                    .gemini_model
                ),

                evidence=(
                    evidence
                ),

                report=(
                    report
                ),
            )
        )

    except psycopg.Error as exc:
        logger.exception(
            (
                "Failed to save investigation "
                "for incident %s"
            ),
            incident_id,
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Investigation generated "
                "but could not be saved"
            ),
        ) from exc

    return {
        "investigation_id":
            investigation_id,

        "incident_id":
            incident_id,

        "model":
            settings.gemini_model,

        "evidence_collected_at":
            evidence[
                "evidence_collected_at"
            ],

        "investigation":
            report.model_dump(
                mode="json"
            ),
    }


@router.get(
    "/by-incident/{incident_id}"
)
def get_incident_investigations(
    incident_id: int,

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    try:
        investigations = (
            list_investigations_for_incident(
                incident_id=(
                    incident_id
                ),
                limit=limit,
            )
        )

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Investigation database "
                "unavailable"
            ),
        ) from exc

    return {
        "incident_id":
            incident_id,

        "count":
            len(
                investigations
            ),

        "investigations":
            investigations,
    }


@router.get(
    "/{investigation_id}"
)
def get_investigation(
    investigation_id: int,
):
    try:
        investigation = (
            get_investigation_by_id(
                investigation_id
            )
        )

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Investigation database "
                "unavailable"
            ),
        ) from exc

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Investigation not found"
            ),
        )

    return investigation


@router.post(
    "/{incident_id}/run-agent"
)
def run_agent_investigation(
    incident_id: int,

    run_id: UUID = Query(
        ...
    ),
):
    thread_id = str(
        run_id
    )

    conninfo = (
        make_conninfo(
            host=(
                settings
                .postgres_host
            ),

            port=(
                settings
                .postgres_port
            ),

            dbname=(
                settings
                .postgres_db
            ),

            user=(
                settings
                .postgres_user
            ),

            password=(
                settings
                .postgres_password
            ),
        )
    )

    config = {
        "configurable": {
            "thread_id":
                thread_id,
        },

        "recursion_limit":
            20,
    }

    try:
        with (
            PostgresSaver
            .from_conn_string(
                conninfo
            )
        ) as checkpointer:

            checkpointer.setup()

            graph = (
                builder.compile(
                    checkpointer=(
                        checkpointer
                    ),
                )
            )

            snapshot = (
                graph.get_state(
                    config
                )
            )

            if snapshot.values:
                if (
                    snapshot.values[
                        "incident_id"
                    ]
                    != incident_id
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Run ID belongs "
                            "to another incident"
                        ),
                    )

                if (
                    snapshot.values.get(
                        "investigation_id"
                    )
                ):
                    result = (
                        snapshot.values
                    )

                else:
                    result = (
                        _invoke_graph_with_metrics(
                            graph,
                            None,
                            config,
                        )
                    )

            else:
                result = (
                    _invoke_graph_with_metrics(
                        graph,

                        {
                            "incident_id":
                                incident_id,

                            "events":
                                [],

                            "tool_history":
                                [],
                        },

                        config,
                    )
                )

    except HTTPException:
        raise

    except psycopg.Error as exc:
        logger.exception(
            (
                "Checkpoint database "
                "error for run %s"
            ),
            thread_id,
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Checkpoint database "
                "unavailable"
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            (
                "Agent investigation "
                "interrupted: %s"
            ),
            thread_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Investigation interrupted. "
                "Retry with the same run_id "
                "after checking backend logs."
            ),
        ) from exc

    return {
        "run_id":
            thread_id,

        "incident_id":
            incident_id,

        "status":
            result.get(
                "status"
            ),

        "investigation_id":
            result.get(
                "investigation_id"
            ),

        "tool_rounds":
            result.get(
                "tool_rounds",
                0,
            ),

        "tool_calls":
            len(
                result.get(
                    "tool_history",
                    [],
                )
            ),
    }
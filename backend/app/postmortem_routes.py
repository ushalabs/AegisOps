import psycopg

from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from app.db.database import get_connection
from app.postmortem import (
    get_postmortem_by_incident,
    search_incident_memories,
)
from app.postmortem_service import (
    generate_and_store_postmortem,
)


router = APIRouter(
    prefix="/postmortems",
    tags=["Postmortems"],
)


@router.post(
    "/incidents/{incident_id}/generate"
)
def generate_incident_postmortem(
    incident_id: int,
):
    if incident_id < 1:
        raise HTTPException(
            status_code=422,
            detail="Invalid incident ID.",
        )

    try:
        result = generate_and_store_postmortem(
            incident_id
        )

    except ValueError as exc:
        message = str(exc)

        if message == "Incident not found.":
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=409,
            detail=message,
        ) from exc

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Postmortem database operation failed."
            ),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Postmortem generation failed."
            ),
        ) from exc

    return result


@router.get(
    "/incidents/{incident_id}"
)
def get_incident_postmortem(
    incident_id: int,
):
    try:
        postmortem = (
            get_postmortem_by_incident(
                incident_id
            )
        )

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Postmortem database unavailable."
            ),
        ) from exc

    if postmortem is None:
        raise HTTPException(
            status_code=404,
            detail="Postmortem not found.",
        )

    return postmortem


@router.get(
    "/incidents/{incident_id}/memory"
)
def get_incident_memory(
    incident_id: int,
):
    try:
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

                memory = cur.fetchone()

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Incident memory database unavailable."
            ),
        ) from exc

    if memory is None:
        raise HTTPException(
            status_code=404,
            detail="Incident memory not found.",
        )

    return memory

@router.get("/search")
def search_historical_incidents(
    query: str = Query(
        ...,
        min_length=3,
        max_length=500,
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=10,
    ),
    exclude_incident_id: int | None = Query(
        default=None,
        ge=1,
    ),
):
    try:
        results = search_incident_memories(
            query=query,
            limit=limit,
            exclude_incident_id=exclude_incident_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Incident memory search unavailable."
            ),
        ) from exc

    return {
        "query": query,
        "count": len(results),
        "results": results,
    }
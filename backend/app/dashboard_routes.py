import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psycopg

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi.security import HTTPBasicCredentials
from psycopg.rows import dict_row

from app.db.database import get_connection
from app.operator_routes import require_operator


router = APIRouter(
    prefix="/dashboard/api",
    tags=["Dashboard"],
)


HTTP_TIMEOUT_SECONDS = 2.0
DOCKER_TIMEOUT_SECONDS = 3.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_http_service(
    *,
    key: str,
    name: str,
    urls: list[str],
):
    last_error = "Service unavailable."

    for url in urls:
        started_at = perf_counter()

        try:
            request = Request(
                url,
                method="GET",
                headers={
                    "User-Agent":
                        "AegisOps-Dashboard/1.0",
                },
            )

            with urlopen(
                request,
                timeout=HTTP_TIMEOUT_SECONDS,
            ) as response:
                status_code = response.status

                latency_ms = round(
                    (
                        perf_counter()
                        - started_at
                    )
                    * 1000,
                    1,
                )

                if 200 <= status_code < 400:
                    return {
                        "key": key,
                        "name": name,
                        "status": "HEALTHY",
                        "detail":
                            f"{latency_ms} ms response",
                        "latency_ms":
                            latency_ms,
                        "checked_at":
                            _utc_now_iso(),
                    }

                last_error = (
                    f"HTTP {status_code}"
                )

        except HTTPError as exc:
            last_error = (
                f"HTTP {exc.code}"
            )

        except URLError as exc:
            reason = (
                exc.reason
                if exc.reason
                else "Connection failed"
            )

            last_error = str(reason)

        except TimeoutError:
            last_error = (
                "Health check timed out"
            )

        except OSError as exc:
            last_error = str(exc)


    return {
        "key": key,
        "name": name,
        "status": "UNHEALTHY",
        "detail": last_error,
        "latency_ms": None,
        "checked_at": _utc_now_iso(),
    }


def _check_docker_health(
    *,
    key: str,
    name: str,
    container_name: str,
):
    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                (
                    "{{if .State.Health}}"
                    "{{.State.Health.Status}}"
                    "{{else}}"
                    "{{.State.Status}}"
                    "{{end}}"
                ),
                container_name,
            ],
            capture_output=True,
            text=True,
            timeout=DOCKER_TIMEOUT_SECONDS,
            check=False,
        )

        if result.returncode != 0:
            message = (
                result.stderr.strip()
                or "Docker inspect failed"
            )

            return {
                "key": key,
                "name": name,
                "status": "UNHEALTHY",
                "detail": message,
                "latency_ms": None,
                "checked_at": _utc_now_iso(),
            }


        docker_status = (
            result.stdout
            .strip()
            .lower()
        )


        if docker_status == "healthy":
            return {
                "key": key,
                "name": name,
                "status": "HEALTHY",
                "detail":
                    "Docker healthcheck passed",
                "latency_ms": None,
                "checked_at": _utc_now_iso(),
            }


        if docker_status == "starting":
            return {
                "key": key,
                "name": name,
                "status": "DEGRADED",
                "detail":
                    "Healthcheck starting",
                "latency_ms": None,
                "checked_at": _utc_now_iso(),
            }


        if docker_status == "running":
            return {
                "key": key,
                "name": name,
                "status": "HEALTHY",
                "detail":
                    "Container running",
                "latency_ms": None,
                "checked_at": _utc_now_iso(),
            }


        return {
            "key": key,
            "name": name,
            "status": "UNHEALTHY",
            "detail":
                f"Container status: {docker_status}",
            "latency_ms": None,
            "checked_at": _utc_now_iso(),
        }


    except subprocess.TimeoutExpired:
        return {
            "key": key,
            "name": name,
            "status": "UNHEALTHY",
            "detail":
                "Docker health check timed out",
            "latency_ms": None,
            "checked_at": _utc_now_iso(),
        }


    except FileNotFoundError:
        return {
            "key": key,
            "name": name,
            "status": "UNHEALTHY",
            "detail":
                "Docker CLI unavailable",
            "latency_ms": None,
            "checked_at": _utc_now_iso(),
        }


    except OSError as exc:
        return {
            "key": key,
            "name": name,
            "status": "UNHEALTHY",
            "detail": str(exc),
            "latency_ms": None,
            "checked_at": _utc_now_iso(),
        }


def _load_service_health():
    checks = [
        lambda: _check_http_service(
            key="benchmark-api",
            name="Benchmark API",
            urls=[
                "http://127.0.0.1:8001/health",
            ],
        ),

        lambda: _check_docker_health(
            key="postgresql",
            name="PostgreSQL",
            container_name=(
                "aegisops-benchmark-db"
            ),
        ),

        lambda: _check_docker_health(
            key="redis",
            name="Redis",
            container_name=(
                "aegisops-benchmark-redis"
            ),
        ),

        lambda: _check_http_service(
            key="prometheus",
            name="Prometheus",
            urls=[
                (
                    "http://127.0.0.1:"
                    "9090/-/healthy"
                ),
            ],
        ),

        lambda: _check_http_service(
            key="grafana",
            name="Grafana",
            urls=[
                (
                    "http://127.0.0.1:"
                    "3000/api/health"
                ),
            ],
        ),

        lambda: _check_http_service(
            key="cadvisor",
            name="cAdvisor",
            urls=[
                (
                    "http://127.0.0.1:"
                    "8080/healthz"
                ),
                (
                    "http://127.0.0.1:"
                    "8080/"
                ),
            ],
        ),
    ]


    with ThreadPoolExecutor(
        max_workers=len(checks)
    ) as executor:
        futures = [
            executor.submit(check)
            for check in checks
        ]

        return [
            future.result()
            for future in futures
        ]


@router.get("/overview")
def get_dashboard_overview(
    hours: int = Query(
        default=24,
        ge=1,
        le=168,
    ),
    _: HTTPBasicCredentials = Depends(
        require_operator
    ),
):
    try:
        with get_connection() as conn:
            with conn.cursor(
                row_factory=dict_row
            ) as cur:

                cur.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (
                            WHERE status = 'OPEN'
                        ) AS open_incidents,

                        COUNT(*) FILTER (
                            WHERE status = 'RESOLVED'
                        ) AS resolved_incidents,

                        COUNT(*) AS total_incidents

                    FROM incidents
                    """
                )

                incident_counts = (
                    cur.fetchone()
                )


                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS investigating

                    FROM incidents AS i

                    WHERE i.status = 'OPEN'

                      AND EXISTS (
                          SELECT 1
                          FROM investigations AS inv
                          WHERE inv.incident_id = i.id
                      )

                      AND NOT EXISTS (
                          SELECT 1
                          FROM remediation_proposals AS rp
                          WHERE rp.incident_id = i.id
                            AND rp.status IN (
                                'PENDING',
                                'APPROVED'
                            )
                      )
                    """
                )

                investigating = (
                    cur.fetchone()
                )


                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS pending_approval

                    FROM remediation_proposals

                    WHERE status = 'PENDING'
                      AND expires_at > NOW()
                    """
                )

                pending = cur.fetchone()


                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS recovered

                    FROM recovery_verifications

                    WHERE status = 'RECOVERED'
                    """
                )

                recovered = (
                    cur.fetchone()
                )


                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS postmortems

                    FROM incident_postmortems
                    """
                )

                postmortems = (
                    cur.fetchone()
                )


                cur.execute(
                    """
                    SELECT
                        id,
                        title,
                        service,
                        severity,
                        status,
                        first_detected_at,
                        last_seen_at,
                        resolved_at

                    FROM incidents

                    WHERE status = 'OPEN'

                    ORDER BY
                        first_detected_at DESC

                    LIMIT 10
                    """
                )

                active_incidents = (
                    cur.fetchall()
                )


                cur.execute(
                    """
                    SELECT
                        id,
                        title,
                        service,
                        severity,
                        status,
                        first_detected_at,
                        last_seen_at,
                        resolved_at

                    FROM incidents

                    WHERE first_detected_at >=
                        NOW() - (
                            %s * INTERVAL '1 hour'
                        )

                    ORDER BY
                        first_detected_at DESC

                    LIMIT 8
                    """,
                    (hours,),
                )

                recent_incidents = (
                    cur.fetchall()
                )


        services = (
            _load_service_health()
        )


        return {
            "range_hours": hours,

            "counts": {
                "open_incidents":
                    incident_counts[
                        "open_incidents"
                    ],

                "investigating":
                    investigating[
                        "investigating"
                    ],

                "pending_approval":
                    pending[
                        "pending_approval"
                    ],

                "recovered":
                    recovered[
                        "recovered"
                    ],

                "postmortems":
                    postmortems[
                        "postmortems"
                    ],

                "total_incidents":
                    incident_counts[
                        "total_incidents"
                    ],
            },

            "services":
                services,

            "active_incidents":
                active_incidents,

            "recent_incidents":
                recent_incidents,
        }


    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Dashboard data unavailable."
            ),
        ) from exc


@router.get("/incidents")
def get_dashboard_incidents(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    _: HTTPBasicCredentials = Depends(
        require_operator
    ),
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
                        title,
                        service,
                        severity,
                        status,
                        first_detected_at,
                        last_seen_at,
                        resolved_at

                    FROM incidents

                    ORDER BY
                        first_detected_at DESC

                    LIMIT %s
                    """,
                    (limit,),
                )

                incidents = (
                    cur.fetchall()
                )


        return {
            "incidents":
                incidents,
        }


    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Incident data unavailable."
            ),
        ) from exc
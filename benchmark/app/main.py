import asyncio
import os
import time
from contextlib import asynccontextmanager

import psycopg
import redis
from fastapi import FastAPI, HTTPException, Query
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel
from starlette.responses import Response


# -------------------------------------------------------------------
# Prometheus metrics
# -------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "benchmark_http_requests_total",
    "Total HTTP requests received by the benchmark API",
    ["method", "path", "status"],
)

REQUEST_DURATION = Histogram(
    "benchmark_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

DEPENDENCY_UP = Gauge(
    "benchmark_dependency_up",
    "Whether a benchmark dependency is available",
    ["dependency"],
)


# -------------------------------------------------------------------
# Request models
# -------------------------------------------------------------------

class ItemCreate(BaseModel):
    name: str


# -------------------------------------------------------------------
# Dependency connections
# -------------------------------------------------------------------

def get_database_connection():
    return psycopg.connect(
        host=os.getenv("BENCHMARK_DB_HOST"),
        port=os.getenv("BENCHMARK_DB_PORT"),
        dbname=os.getenv("BENCHMARK_DB_NAME"),
        user=os.getenv("BENCHMARK_DB_USER"),
        password=os.getenv("BENCHMARK_DB_PASSWORD"),
        connect_timeout=2,
    )


def get_redis_client():
    return redis.Redis(
        host=os.getenv("BENCHMARK_REDIS_HOST"),
        port=int(os.getenv("BENCHMARK_REDIS_PORT", "6379")),
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )


# -------------------------------------------------------------------
# Dependency health checks
# -------------------------------------------------------------------

def check_postgresql() -> bool:
    try:
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()

        return True

    except psycopg.Error:
        return False


def check_redis() -> bool:
    try:
        redis_client = get_redis_client()
        redis_client.ping()

        return True

    except redis.RedisError:
        return False


# -------------------------------------------------------------------
# Benchmark database setup
# -------------------------------------------------------------------

def ensure_items_table():
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS benchmark_items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )


# -------------------------------------------------------------------
# Background dependency monitoring
# -------------------------------------------------------------------

async def monitor_dependencies():
    while True:
        postgresql_up, redis_up = await asyncio.gather(
            asyncio.to_thread(check_postgresql),
            asyncio.to_thread(check_redis),
        )

        DEPENDENCY_UP.labels(
            dependency="postgresql"
        ).set(1 if postgresql_up else 0)

        DEPENDENCY_UP.labels(
            dependency="redis"
        ).set(1 if redis_up else 0)

        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(
        monitor_dependencies()
    )

    try:
        yield

    finally:
        monitor_task.cancel()

        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


# -------------------------------------------------------------------
# FastAPI application
# -------------------------------------------------------------------

app = FastAPI(
    title="AegisOps Benchmark API",
    version="0.1.0",
    lifespan=lifespan,
)


# -------------------------------------------------------------------
# Prometheus middleware
# -------------------------------------------------------------------

@app.middleware("http")
async def collect_request_metrics(request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        path=request.url.path,
    ).observe(duration)

    return response


# -------------------------------------------------------------------
# Health / readiness
# -------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "benchmark-api",
    }


@app.get("/ready")
def readiness_check():
    if not check_postgresql():
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL unavailable",
        )

    if not check_redis():
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable",
        )

    return {
        "status": "ready",
        "postgresql": "connected",
        "redis": "connected",
    }


# -------------------------------------------------------------------
# PostgreSQL benchmark operations
# -------------------------------------------------------------------

@app.post("/items")
def create_item(item: ItemCreate):
    try:
        ensure_items_table()

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO benchmark_items (name)
                    VALUES (%s)
                    RETURNING id, name, created_at;
                    """,
                    (item.name,),
                )

                created_item = cursor.fetchone()

        return {
            "id": created_item[0],
            "name": created_item[1],
            "created_at": created_item[2],
        }

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL operation failed",
        )


@app.get("/items")
def get_items():
    try:
        ensure_items_table()

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, created_at
                    FROM benchmark_items
                    ORDER BY id DESC
                    LIMIT 20;
                    """
                )

                rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "created_at": row[2],
            }
            for row in rows
        ]

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL operation failed",
        )


# -------------------------------------------------------------------
# Redis benchmark operation
# -------------------------------------------------------------------

@app.get("/activity")
def get_activity():
    try:
        redis_client = get_redis_client()

        request_count = redis_client.incr(
            "benchmark:activity_requests"
        )

        return {
            "activity_requests": request_count,
        }

    except redis.RedisError:
        raise HTTPException(
            status_code=503,
            detail="Redis operation failed",
        )


# -------------------------------------------------------------------
# Controlled failure simulations
# -------------------------------------------------------------------

@app.get("/simulate/error")
def simulate_error():
    raise HTTPException(
        status_code=500,
        detail="Simulated internal server error",
    )


@app.get("/simulate/slow")
async def simulate_slow_response(
    seconds: int = Query(default=5, ge=1, le=30),
):
    await asyncio.sleep(seconds)

    return {
        "status": "completed",
        "delay_seconds": seconds,
    }


# -------------------------------------------------------------------
# Prometheus endpoint
# -------------------------------------------------------------------

@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
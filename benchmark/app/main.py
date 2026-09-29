import os

import psycopg
import asyncio
import redis
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


app = FastAPI(
    title="AegisOps Benchmark API",
    version="0.1.0",
)


class ItemCreate(BaseModel):
    name: str


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
        decode_responses=True,
    )


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


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "benchmark-api",
    }


@app.get("/ready")
def readiness_check():
    try:
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()

    except psycopg.Error:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL unavailable",
        )

    try:
        redis_client = get_redis_client()
        redis_client.ping()

    except redis.RedisError:
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable",
        )

    return {
        "status": "ready",
        "postgresql": "connected",
        "redis": "connected",
    }


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
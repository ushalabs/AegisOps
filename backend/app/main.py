from fastapi import FastAPI, HTTPException
from app.incidents.routes import router as incidents_router

from app.db.database import check_database_connection

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.incidents.routes import router as incidents_router
from app.incidents.worker import incident_detection_worker
from app.investigations.routes import router as investigation_router
from app.remediation_routes import router as remediation_router
from app.operator_routes import router as operator_router
from app.postmortem_routes import (
    router as postmortem_router,
)

from app.dashboard_routes import (
    router as dashboard_router,
)

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)

from starlette.responses import Response

@asynccontextmanager
async def lifespan(app: FastAPI):
    detection_task = asyncio.create_task(
        incident_detection_worker()
    )

    try:
        yield

    finally:
        detection_task.cancel()

        try:
            await detection_task

        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="AegisOps API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(incidents_router)
app.include_router(investigation_router)
app.include_router(remediation_router)
app.include_router(operator_router)
app.include_router(postmortem_router)
app.include_router(dashboard_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "aegisops-api",
    }


@app.get("/ready")
def readiness_check():
    if not check_database_connection():
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )

    return {
        "status": "ready",
        "database": "connected",
    }

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
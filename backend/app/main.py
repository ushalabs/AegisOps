from fastapi import FastAPI, HTTPException

from app.db.database import check_database_connection


app = FastAPI(
    title="AegisOps API",
    version="0.1.0",
)


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
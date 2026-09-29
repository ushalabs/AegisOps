from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "aegisops-api",
    }


def test_readiness_when_database_available(monkeypatch):
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: True,
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
    }


def test_readiness_when_database_unavailable(monkeypatch):
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: False,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database unavailable",
    }
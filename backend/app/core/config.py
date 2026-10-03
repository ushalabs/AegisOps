import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(ENV_FILE)


class Settings:
    app_name = os.getenv("APP_NAME", "AegisOps")
    app_env = os.getenv("APP_ENV", "development")

    postgres_db = os.getenv("POSTGRES_DB")
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    prometheus_url: str = os.getenv(
        "PROMETHEUS_URL",
        "http://127.0.0.1:9090",)

    incident_detection_interval_seconds: int = int(
        os.getenv("INCIDENT_DETECTION_INTERVAL_SECONDS", "10")
    )

    n8n_incident_webhook_url: str = os.getenv(
    "N8N_INCIDENT_WEBHOOK_URL",
    "http://127.0.0.1:5678/webhook/aegisops-incident",
    )

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
    )


settings = Settings()
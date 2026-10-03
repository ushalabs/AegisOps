
from psycopg.types.json import Jsonb
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from app.db.database import get_connection
from app.knowledge.repository import upsert_documents


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

DOCUMENTS = [
    {
        "source_key": "sample:redis",
        "title": "Redis Connection Troubleshooting",
        "content": (
            "When an application cannot connect to Redis, "
            "check the Redis container status, inspect Redis "
            "logs, review application connection errors, "
            "and verify network connectivity."
        ),
    },
    {
        "source_key": "sample:postgresql",
        "title": "PostgreSQL Connection Troubleshooting",
        "content": (
            "When PostgreSQL becomes unavailable, inspect "
            "database readiness, container logs, connection "
            "limits, credentials, and database connectivity."
        ),
    },
    {
        "source_key": "sample:api-latency",
        "title": "API Latency Troubleshooting",
        "content": (
            "When API response times increase, inspect "
            "request latency metrics, slow endpoints, "
            "dependency response times, and resource usage."
        ),
    },
]



def main():
    document_ids = upsert_documents(
        DOCUMENTS,
        source_type="sample_runbook",
        metadata={
            "environment": "benchmark",
            "sample": True,
        },
    )

    for document, document_id in zip(
        DOCUMENTS,
        document_ids,
    ):
        print(
            f"Stored document {document_id}: "
            f"{document['title']}"
        )


if __name__ == "__main__":
    main()
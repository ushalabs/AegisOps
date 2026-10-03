
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from app.db.database import get_connection
from app.knowledge.embeddings import (
    EMBEDDING_MODEL,
    embed_texts,
)


def upsert_documents(
    documents: list[dict],
    source_type: str,
    metadata: dict | None = None,
) -> list[int]:
    if not documents:
        return []

    embeddings = embed_texts([
        document["content"]
        for document in documents
    ])

    document_ids = []

    with get_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            for document, embedding in zip(
                documents,
                embeddings,
            ):
                cursor.execute(
                    """
                    INSERT INTO knowledge_documents (
                        source_key,
                        title,
                        content,
                        source_type,
                        embedding_model,
                        embedding,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_key)
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        source_type = EXCLUDED.source_type,
                        embedding_model = EXCLUDED.embedding_model,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    RETURNING id;
                    """,
                    (
                        document["source_key"],
                        document["title"],
                        document["content"],
                        source_type,
                        EMBEDDING_MODEL,
                        embedding,
                        Jsonb(
                            document.get(
                                "metadata",
                                metadata or {},
                            )
                        ),
                    ),
                )

                document_ids.append(
                    cursor.fetchone()[0]
                )

    return document_ids
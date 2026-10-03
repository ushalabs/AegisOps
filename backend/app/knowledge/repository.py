
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from app.db.database import get_connection
from app.knowledge.embeddings import (
    EMBEDDING_MODEL,
    embed_texts,
    embed_query,
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


def replace_document_chunks(
    document_id: int,
    chunks: list[dict],
) -> int:
    if not chunks:
        raise ValueError("Document has no chunks to store")

    embeddings = embed_texts([
        chunk["content"]
        for chunk in chunks
    ])

    with get_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            for chunk, embedding in zip(
                chunks,
                embeddings,
            ):
                cursor.execute(
                    """
                    INSERT INTO knowledge_chunks (
                        document_id,
                        chunk_index,
                        heading,
                        content,
                        embedding_model,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, chunk_index)
                    DO UPDATE SET
                        heading = EXCLUDED.heading,
                        content = EXCLUDED.content,
                        embedding_model = EXCLUDED.embedding_model,
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW();
                    """,
                    (
                        document_id,
                        chunk["chunk_index"],
                        chunk["heading"],
                        chunk["content"],
                        EMBEDDING_MODEL,
                        embedding,
                    ),
                )

            # Remove obsolete chunks if the document
            # now contains fewer sections than before.
            cursor.execute(
                """
                DELETE FROM knowledge_chunks
                WHERE document_id = %s
                  AND chunk_index >= %s;
                """,
                (document_id, len(chunks)),
            )

    return len(chunks)


def search_knowledge_chunks(
    query: str,
    limit: int = 3,
) -> list[dict]:
    if not query.strip():
        raise ValueError("Search query cannot be empty")

    if not 1 <= limit <= 10:
        raise ValueError("Limit must be between 1 and 10")

    query_embedding = embed_query(query)

    with get_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    c.id,
                    c.document_id,
                    d.source_key,
                    d.title,
                    c.heading,
                    c.content,
                    1 - (c.embedding <=> %s) AS similarity
                FROM knowledge_chunks AS c
                JOIN knowledge_documents AS d
                    ON d.id = c.document_id
                WHERE d.source_type = 'runbook'
                  AND c.embedding_model = %s
                ORDER BY c.embedding <=> %s
                LIMIT %s;
                """,
                (
                    query_embedding,
                    EMBEDDING_MODEL,
                    query_embedding,
                    limit,
                ),
            )

            rows = cursor.fetchall()

    return [
        {
            "chunk_id": row[0],
            "document_id": row[1],
            "source_key": row[2],
            "title": row[3],
            "heading": row[4],
            "content": row[5],
            "similarity": float(row[6]),
        }
        for row in rows
    ]


CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id BIGSERIAL PRIMARY KEY,

    document_id BIGINT NOT NULL
        REFERENCES knowledge_documents(id)
        ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    heading TEXT NOT NULL,
    content TEXT NOT NULL,

    embedding_model TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (document_id, chunk_index)
);

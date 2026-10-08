CREATE TABLE IF NOT EXISTS incident_memories (
    id BIGSERIAL PRIMARY KEY,

    incident_id BIGINT NOT NULL UNIQUE
        REFERENCES incidents(id)
        ON DELETE CASCADE,

    postmortem_id BIGINT NOT NULL UNIQUE
        REFERENCES incident_postmortems(id)
        ON DELETE CASCADE,

    memory_text TEXT NOT NULL,

    embedding_model TEXT NOT NULL,

    embedding VECTOR(384) NOT NULL,

    metadata JSONB NOT NULL
        DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS
    idx_incident_memories_incident_id
ON incident_memories (
    incident_id
);
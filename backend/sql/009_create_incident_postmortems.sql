CREATE TABLE IF NOT EXISTS incident_postmortems (
    id BIGSERIAL PRIMARY KEY,

    incident_id BIGINT NOT NULL UNIQUE
        REFERENCES incidents(id)
        ON DELETE CASCADE,

    timeline JSONB NOT NULL,

    summary TEXT NOT NULL,

    root_cause TEXT,

    impact TEXT,

    what_went_well JSONB NOT NULL
        DEFAULT '[]'::jsonb,

    what_went_wrong JSONB NOT NULL
        DEFAULT '[]'::jsonb,

    lessons_learned JSONB NOT NULL
        DEFAULT '[]'::jsonb,

    preventive_actions JSONB NOT NULL
        DEFAULT '[]'::jsonb,

    model VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS
    idx_incident_postmortems_created_at
ON incident_postmortems (
    created_at DESC
);
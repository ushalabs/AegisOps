
CREATE TABLE IF NOT EXISTS investigations (
    id BIGSERIAL PRIMARY KEY,
    incident_id BIGINT NOT NULL
        REFERENCES incidents(id),
    model VARCHAR(100) NOT NULL,
    evidence_collected_at TIMESTAMPTZ NOT NULL,
    evidence JSONB NOT NULL,
    report JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS
    idx_investigations_incident_created
ON investigations (incident_id, created_at DESC);

CREATE TABLE IF NOT EXISTS remediation_executions (
    id BIGSERIAL PRIMARY KEY,

    proposal_id BIGINT NOT NULL UNIQUE
        REFERENCES remediation_proposals(id),

    incident_id BIGINT NOT NULL
        REFERENCES incidents(id),

    action_key TEXT NOT NULL,
    target_service TEXT NOT NULL,

    status VARCHAR(20) NOT NULL
        CHECK (
            status IN (
                'RUNNING',
                'SUCCEEDED',
                'FAILED'
            )
        ),

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,

    exit_code INTEGER,
    output TEXT,
    error TEXT
);

CREATE INDEX IF NOT EXISTS
    idx_remediation_executions_incident
ON remediation_executions (incident_id);
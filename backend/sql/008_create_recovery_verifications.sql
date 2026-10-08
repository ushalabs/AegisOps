CREATE TABLE IF NOT EXISTS recovery_verifications (
    id BIGSERIAL PRIMARY KEY,

    execution_id BIGINT NOT NULL UNIQUE
        REFERENCES remediation_executions(id)
        ON DELETE CASCADE,

    incident_id BIGINT NOT NULL
        REFERENCES incidents(id)
        ON DELETE CASCADE,

    rule_key TEXT NOT NULL,

    status TEXT NOT NULL
        DEFAULT 'VERIFYING'
        CHECK (
            status IN (
                'VERIFYING',
                'RECOVERED',
                'NOT_RECOVERED',
                'INCONCLUSIVE'
            )
        ),

    attempt_count INTEGER NOT NULL
        DEFAULT 0
        CHECK (attempt_count >= 0),

    consecutive_healthy INTEGER NOT NULL
        DEFAULT 0
        CHECK (consecutive_healthy >= 0),

    last_observed_value DOUBLE PRECISION,

    evidence JSONB NOT NULL
        DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    first_checked_at TIMESTAMPTZ,

    last_checked_at TIMESTAMPTZ,

    verified_at TIMESTAMPTZ
);


CREATE INDEX IF NOT EXISTS
    idx_recovery_verifications_incident_id
ON recovery_verifications (
    incident_id
);


CREATE INDEX IF NOT EXISTS
    idx_recovery_verifications_status
ON recovery_verifications (
    status
);
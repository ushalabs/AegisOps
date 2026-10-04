
CREATE TABLE IF NOT EXISTS remediation_proposals (
    id BIGSERIAL PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES incidents(id),

    investigation_id BIGINT NOT NULL
        REFERENCES investigations(id),

    action_key TEXT NOT NULL,
    target_service TEXT NOT NULL,

    rationale TEXT NOT NULL,
    expected_outcome TEXT NOT NULL,

    risk_level VARCHAR(20) NOT NULL
        CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),

    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (
            status IN (
                'PENDING',
                'APPROVED',
                'REJECTED',
                'EXPIRED',
                'CANCELLED'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
        DEFAULT (NOW() + INTERVAL '24 hours'),

    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_note TEXT,

    CONSTRAINT valid_action_target CHECK (
        (
            action_key = 'restart_benchmark_redis'
            AND target_service = 'benchmark-redis'
        )
        OR (
            action_key = 'restart_benchmark_postgresql'
            AND target_service = 'benchmark-postgresql'
        )
        OR (
            action_key = 'restart_benchmark_api'
            AND target_service = 'benchmark-api'
        )
    ),

    CONSTRAINT valid_expiration CHECK (
        expires_at > created_at
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS
    unique_pending_remediation
ON remediation_proposals (incident_id, action_key)
WHERE status = 'PENDING';

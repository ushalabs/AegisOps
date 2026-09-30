CREATE TABLE IF NOT EXISTS incidents (
    id BIGSERIAL PRIMARY KEY,

    fingerprint VARCHAR(255) NOT NULL,
    rule_key VARCHAR(100) NOT NULL,

    title VARCHAR(255) NOT NULL,
    service VARCHAR(150) NOT NULL,

    severity VARCHAR(20) NOT NULL
        CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),

    status VARCHAR(20) NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'RESOLVED')),

    trigger_value DOUBLE PRECISION,
    threshold DOUBLE PRECISION NOT NULL,

    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS unique_open_incident_fingerprint
ON incidents (fingerprint)
WHERE status = 'OPEN';
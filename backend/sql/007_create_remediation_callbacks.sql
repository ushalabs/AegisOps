CREATE TABLE IF NOT EXISTS remediation_callbacks (
    proposal_id BIGINT PRIMARY KEY
        REFERENCES remediation_proposals(id)
        ON DELETE CASCADE,

    resume_url TEXT NOT NULL,

    registered_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    resumed_at TIMESTAMPTZ
);
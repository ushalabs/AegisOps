CREATE TABLE IF NOT EXISTS eval_runs (
    id BIGSERIAL PRIMARY KEY,

    suite_name TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (
            status IN (
                'RUNNING',
                'COMPLETED',
                'FAILED'
            )
        ),

    total_cases INTEGER NOT NULL DEFAULT 0,
    passed_cases INTEGER NOT NULL DEFAULT 0,
    failed_cases INTEGER NOT NULL DEFAULT 0,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);


CREATE TABLE IF NOT EXISTS eval_results (
    id BIGSERIAL PRIMARY KEY,

    eval_run_id BIGINT NOT NULL
        REFERENCES eval_runs(id)
        ON DELETE CASCADE,

    incident_id BIGINT
        REFERENCES incidents(id)
        ON DELETE SET NULL,

    investigation_id BIGINT
        REFERENCES investigations(id)
        ON DELETE SET NULL,

    case_key TEXT NOT NULL,

    passed BOOLEAN NOT NULL,

    score DOUBLE PRECISION NOT NULL
        CHECK (
            score >= 0
            AND score <= 1
        ),

    checks JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS
    idx_eval_results_run_id
ON eval_results(eval_run_id);


CREATE INDEX IF NOT EXISTS
    idx_eval_results_incident_id
ON eval_results(incident_id);


CREATE INDEX IF NOT EXISTS
    idx_eval_results_investigation_id
ON eval_results(investigation_id);
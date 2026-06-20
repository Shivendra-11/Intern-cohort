CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    payload JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO jobs (payload, status) VALUES ('{"seed": true}', 'processed')
ON CONFLICT DO NOTHING;

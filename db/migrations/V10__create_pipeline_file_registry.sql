CREATE TABLE IF NOT EXISTS pipeline_file_registry (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    CONSTRAINT uq_pipeline_file UNIQUE (pipeline_name, file_name, status)
);
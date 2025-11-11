CREATE TABLE IF NOT EXISTS pipeline_file_registry (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    CONSTRAINT uq_pipeline_file UNIQUE (pipeline_name, filename, status)
);

COMMENT ON TABLE pipeline_file_registry IS 'Historique des exécutions de pipelines ETL';
COMMENT ON COLUMN pipeline_file_registry.pipeline_name IS 'Nom de la pipeline exécutée';
COMMENT ON COLUMN pipeline_file_registry.file_name IS 'Nom du fichier traité';
COMMENT ON COLUMN pipeline_file_registry.status IS 'Statut de la tâche (running, success, error)';

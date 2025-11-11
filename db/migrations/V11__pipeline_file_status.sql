ALTER TABLE pipeline_file_registry
ADD COLUMN status VARCHAR(50) DEFAULT 'pending';

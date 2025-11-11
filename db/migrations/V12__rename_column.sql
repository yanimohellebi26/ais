DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'pipeline_file_registry'
          AND column_name = 'file_name'
    ) THEN
        EXECUTE 'ALTER TABLE pipeline_file_registry RENAME COLUMN file_name TO filename';
    END IF;
END $$ LANGUAGE plpgsql;

ALTER TABLE pipeline_file_registry
DROP CONSTRAINT IF EXISTS uq_pipeline_file;

ALTER TABLE pipeline_file_registry
ADD CONSTRAINT uq_pipeline_file UNIQUE (pipeline_name, filename, status);

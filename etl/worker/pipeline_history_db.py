from sqlalchemy import text

from utils.db import get_session


class PipelineHistoryDB:
    @staticmethod
    def check_if_running(pipeline_name, files):
        with get_session() as session:
            results = session.execute(
                text("""
                    SELECT file_name 
                    FROM pipeline_file_registry
                    WHERE pipeline_name = :p 
                      AND file_name = ANY(:files)
                      AND status IN ('success','running')
                """),
                {"p": pipeline_name, "files": files},
            ).fetchall()
            return [row[0] for row in results]

    @staticmethod
    def insert_history_running(pipeline_name, file):
        with get_session() as session:
            session.execute(
                text("""
                    INSERT INTO pipeline_file_registry (pipeline_name, file_name, status, created_at)
                    VALUES (:p, :f, 'running', NOW())
                    ON CONFLICT (pipeline_name, file_name) DO NOTHING
                """),
                {"p": pipeline_name, "f": file}
            )
            session.commit()


    @staticmethod
    def delete_registry_entry(pipeline_name, file):
        with get_session() as session:
            session.execute(
                text("""
                    DELETE FROM pipeline_file_registry
                    WHERE pipeline_name = :p AND file_name = :f
                """),
                {"p": pipeline_name, "f": file}
            )
            session.commit()


    @staticmethod
    def mark_success(pipeline_name, file):
        with get_session() as session:
            session.execute(
                text("""
                    UPDATE pipeline_file_registry
                    SET status='success', ended_at=NOW()
                    WHERE pipeline_name=:p AND file_name=:f
                """),
                {"p": pipeline_name, "f": file}
            )
            session.commit()
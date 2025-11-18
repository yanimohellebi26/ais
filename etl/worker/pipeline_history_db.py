from sqlalchemy import text

from utils.db import get_session


class PipelineHistoryDB:
    @staticmethod
    def check_if_running(pipeline_name, file):
        with get_session() as session:
            existing = session.execute(
                text("""
                           SELECT 1 FROM pipeline_file_registry
                           WHERE pipeline_name = :p AND file_name = :f AND status IN ('success','running')
                       """),
                {"p": pipeline_name, "f": file}
            ).scalar()

            if existing:
                raise Exception()


    @staticmethod
    def insert_history_running(pipeline_name, file):
        with get_session() as session:
            session.execute(
                text("""
                    INSERT INTO pipeline_file_registry (pipeline_name, file_name, status, created_at)
                    VALUES (:p, :f, 'running', NOW())
                """),
                {"p": pipeline_name, "f": file}
            )
            session.commit()


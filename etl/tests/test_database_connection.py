# test_db.py
import pytest

from etl.utils.db import DBSession

def test_database_connection():
    db = DBSession()
    try:
        with db.get_session() as session:
            result = session.execute("SELECT 1 as test")
            row = result.fetchone()
            assert row["test"] == 1
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

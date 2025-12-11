# test_db.py
from sqlalchemy import text
import pytest
from etl.utils.db import get_session

def test_database_connection():
    try:
        with get_session() as session:
            result = session.execute(text("SELECT 1 as test")).mappings().first()
            assert result["test"] == 1
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

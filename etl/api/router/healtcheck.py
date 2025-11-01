from fastapi import APIRouter
from utils.db import engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import asyncio

router = APIRouter()

async def test_db_connection():
    loop = asyncio.get_event_loop()

    def check():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return "ok"
        except SQLAlchemyError as e:
            return f"error: {str(e)}"

    return await loop.run_in_executor(None, check)

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

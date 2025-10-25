import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from datetime import datetime
from etl.utils.logger import Logger
from api.security_api import verify_api_key

router = APIRouter()

@router.get("/{date}", response_class=PlainTextResponse)
async def get_logs_by_date(date: str,auth=Depends(verify_api_key)):
    """
    Return all logs for a date.
    Date to format YYYY-MM-DD
    """
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format")


    log_file = Logger.get_log_file(date)

    print(f"log_file: {log_file}")
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail=f"No log file found for {date}")

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {e}")

    return PlainTextResponse(content)

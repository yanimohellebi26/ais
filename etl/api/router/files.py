import os
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from api.security_api import verify_api_key

router = APIRouter()
DOWNLOADS_DIR = "data/downloads"

DATE_PATTERN = re.compile(r"AIS_(\d{4})_(\d{2})_(\d{2})")

@router.get("/")
async def get_files(auth=Depends(verify_api_key)):
    """
    Return all available files in /data/downloads as a JSON array, order by date when possible.
    """
    try:
        if not os.path.exists(DOWNLOADS_DIR):
            raise HTTPException(status_code=404, detail="Downloads directory not found")

        files = [
            f for f in os.listdir(DOWNLOADS_DIR)
            if os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
        ]

        # sort
        def extract_date(filename):
            match = DATE_PATTERN.search(filename)
            if match:
                try:
                    return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                except ValueError:
                    pass
            # no date go to last
            return datetime.min

        files.sort(key=extract_date, reverse=True)

        return files

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error while listing files")

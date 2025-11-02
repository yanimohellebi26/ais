import os
from fastapi import APIRouter, HTTPException, Depends
from api.security_api import verify_api_key

router = APIRouter()

DOWNLOADS_DIR = "data/downloads"

@router.get("/")
async def get_files(auth=Depends(verify_api_key)):
    """
    Return all available files in /data/downloads as a JSON array.
    """
    try:
        if not os.path.exists(DOWNLOADS_DIR):
            raise HTTPException(status_code=404, detail="Downloads directory not found")

        files = [
            f for f in os.listdir(DOWNLOADS_DIR)
            if os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
        ]

        return files

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error while listing files")

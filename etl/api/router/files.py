import os
import re
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from api.security_api import verify_api_key

router = APIRouter()
DOWNLOADS_DIR = "data/downloads"

DATE_PATTERN = re.compile(r"AIS_(\d{4})_(\d{2})_(\d{2})")

@router.get("/")
async def get_files(auth=Depends(verify_api_key)):
    """
    Return all available files in /data/downloads with their size and list of columns.
    """
    try:
        if not os.path.exists(DOWNLOADS_DIR):
            raise HTTPException(status_code=404, detail="Downloads directory not found")

        files = [
            f for f in os.listdir(DOWNLOADS_DIR)
            if os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
        ]

        def extract_date(filename):
            match = DATE_PATTERN.search(filename)
            if match:
                try:
                    return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                except ValueError:
                    pass
            return datetime.min

        files.sort(key=extract_date, reverse=True)

        result = []
        for f in files:
            file_path = os.path.join(DOWNLOADS_DIR, f)
            columns = []
            size_bytes = os.path.getsize(file_path)

            try:
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    first_line = csvfile.readline()
                    if first_line:
                        sep = ';' if ';' in first_line else ','
                        columns = next(csv.reader([first_line], delimiter=sep))
            except Exception:
                columns = []

            result.append({
                "filename": f,
                "size_bytes": size_bytes,
                "columns": columns
            })

        return result

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error while listing files")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), auth=Depends(verify_api_key)):
    """
    Upload a CSV or ZIP file into the downloads directory.
    Accept files with .csv, .zip
    """
    allowed_extensions = (".csv", ".zip")

    try:
        if not file.filename.lower().endswith(allowed_extensions):
            raise HTTPException(status_code=400, detail="Only CSV or ZIP files are allowed")

        if not os.path.exists(DOWNLOADS_DIR):
            os.makedirs(DOWNLOADS_DIR, exist_ok=True)

        file_path = os.path.join(DOWNLOADS_DIR, file.filename)

        with open(file_path, "wb") as f:
            while contents := await file.read(1024 * 1024):  # read in 1MB chunks
                f.write(contents)

        return {"filename": file.filename, "message": "File uploaded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error uploading file")

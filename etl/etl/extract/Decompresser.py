import os
import pandas as pd
import zipfile
from pathlib import Path

from etl.models.context import PipelineContext

def decompress_WDPA_zip(context: PipelineContext) -> PipelineContext:
    """
    Decompresses a WDPA .zip archive and his subarchives if any exists.
    """
    archive_path = Path("data/downloads/") / context.file
    if not archive_path.is_file():
        raise ValueError(f"Archive not found: {archive_path}")

    extract_to = Path("data/downloads/WDPA_Data")
    extract_to.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(archive_path, 'r') as main_zip:        
        for file_name in main_zip.namelist():
            if file_name.endswith('.zip'):
                main_zip.extract(file_name, extract_to)

    for i, file in enumerate(extract_to.glob("*.zip")):
        extract_to_sub = extract_to / f"{i}"
        extract_to_sub.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(file, 'r') as sub_zip:
            sub_zip.extractall(extract_to_sub)
        file.unlink()

    return context
            

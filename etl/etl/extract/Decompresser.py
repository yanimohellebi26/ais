import os
import pandas as pd
import zipfile
from pathlib import Path

from etl.models.context import PipelineContext

def decompress_archive_zip(context: PipelineContext) -> PipelineContext:
    """
    Decompresses a .zip archive and his subarchives if any exists.
    """
    archive_path = Path(context.file)
    if not archive_path.is_file():
        raise ValueError(f"Archive not found: {archive_path}")

    
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(archive_path)

    for file in os.listdir(archive_path):
        if file.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(archive_path)

    return context
            

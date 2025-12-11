import os
from pathlib import Path
import pandas as pd

from etl.models.context import PipelineContext


def extract_data_from_file(context: PipelineContext, selected_map: list[str], separator=',') -> PipelineContext:
    file = context.file
    if not file:
        raise ValueError("No file provided in context")

    file_path = Path(file)

    if not file_path.is_file():
        download_folder = "data/downloads"
        file_path = Path(download_folder) / file_path.name
        if not file_path.is_file():
            raise ValueError(f"File not found: {file_path}")

    file_path = file_path.resolve()

    # Extract file
    new_data = pd.read_csv(file_path,sep=separator)
    new_data = new_data[list(selected_map)]

    context.df = new_data
    return context

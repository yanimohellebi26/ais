import os
from pathlib import Path

import pandas as pd

from etl.models.context import VesselContext


def extract_vessels(context: VesselContext, **kwargs) -> VesselContext:
    file = context.file
    if not file:
        raise ValueError("No file provided in context")

    file_path = Path(file)

    if not file_path.is_file():
        download_folder = os.environ.get("AIS_DOWNLOAD_FOLDER")
        if not download_folder:
            raise ValueError("AIS_DOWNLOAD_FOLDER environment variable is not set")
        file_path = Path(download_folder) / file_path.name
        if not file_path.is_file():
            raise ValueError(f"File not found: {file_path}")

    file_path = file_path.resolve()

    # Pre-processing
    selected_map = [ "mmsi", "last_update", "vessel_name", "imo", "call_sign",
        "vessel_type_id", "length", "width", "draft", "cargo_type_id","transceiver_class",
    ]

    # Extract file
    new_data = pd.read_csv(file_path)
    new_data = new_data[list(selected_map)]

    context.df = new_data
    return context

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class VesselContext:
    """
    Context object used to pass data and metadata between tasks in the
    'load_vessels' ETL workflow.

    Attributes:
        file (Optional[str]): Path to the input CSV file for vessel data.
        df (Optional[pd.DataFrame]): DataFrame containing the newly extracted vessel data.
        df_db (Optional[pd.DataFrame]): DataFrame containing the current vessels from the database.
        workflow_id (Optional[str]): Unique identifier for this workflow execution.
    """
    file: Optional[str] = None
    df: Optional[pd.DataFrame] = None
    df_db: Optional[pd.DataFrame] = None
    workflow_id: Optional[str] = None

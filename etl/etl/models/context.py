from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


@dataclass
class PipelineContext:
    """
    Context object used to pass data and metadata between tasks in the
    'load_vessels' ETL workflow.

    Attributes:
        file (Optional[str]): Path to the input CSV file for vessel data.
        df (Optional[pd.DataFrame]): DataFrame containing the newly extracted vessel data.
        df_db (Optional[pd.DataFrame]): DataFrame containing the current vessels from the database.
    """
    file: Optional[str] = None
    df: Optional[pd.DataFrame] = field(default_factory=pd.DataFrame)
    df_db: Optional[pd.DataFrame] = field(default_factory=pd.DataFrame)

    pa_infos: Optional[pd.DataFrame] = field(default_factory=pd.DataFrame)
    protected_area: Optional[pd.DataFrame] = field(default_factory=pd.DataFrame)

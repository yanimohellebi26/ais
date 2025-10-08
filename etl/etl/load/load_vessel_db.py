from typing import List, Optional, Dict, Tuple

import pandas as pd
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert

from etl.models.context import VesselContext
from etl.utils.db import get_session, engine
from etl.utils.logger import Logger


def _split_table(fullname: str) -> Tuple[Optional[str], str]:
    if "." in fullname:
        schema, table = fullname.split(".", 1)
        return schema, table
    return None, fullname

import numpy as np

def normalize_types(df: pd.DataFrame):
    df = df.copy()
    for col in df.columns:
        # Si la colonne est float mais ne contient que des valeurs entières → convertir en int
        if df[col].dtype == "float64":
            # Vérifie que toutes les valeurs non nulles sont entières
            if all(df[col].dropna().apply(lambda x: float(x).is_integer())):
                df[col] = df[col].astype("Int64")  # int nullable (compatible NaN)
        # Convertit les NaN textuels en None
        if df[col].dtype == "object":
            df[col] = df[col].replace({np.nan: None, "nan": None})
    return df


def load_vessel_to_db(
    context: VesselContext,
    table: str,
    upsert_keys: Optional[List[str]] = None,
    column_mapping: Optional[Dict[str, str]] = None,
    chunk_size: int = 10_000):
    """
    Insert (or upsert) a pandas DataFrame into a Postgres table using SQLAlchemy.
    Raises:
        ValueError: if inputs are invalid.
    """
    data = context.df
    data = normalize_types(data)

    if data.empty:
        raise ValueError("`data` is empty.")
    if not table or not isinstance(table, str):
        raise ValueError("`table` must be a non-empty string like 'schema.table' or 'table'.")
    if chunk_size <= 0:
        raise ValueError("`chunk_size` must be a positive integer.")

    if column_mapping:
        rename_map = {k: v for k, v in column_mapping.items() if k in data.columns}
        if rename_map:
            data.rename(columns=rename_map, inplace=True)

    schema, tbl_name = _split_table(table)

    total = 0
    with get_session() as session:
        metadata = MetaData()
        tbl = Table(tbl_name, metadata, autoload_with=session.bind, schema=schema)

        db_cols = [c.name for c in tbl.columns]
        target_cols = [c for c in db_cols if c in data.columns]
        if not target_cols:
            raise ValueError(
                f"No common columns between DataFrame and target table '{table}'. "
                f"DF columns={list(data.columns)}; DB columns={db_cols}"
            )

        if upsert_keys:
            missing = [k for k in upsert_keys if k not in target_cols]
            if missing:
                raise ValueError(
                    f"`upsert_keys` not found in insertable columns: missing={missing}; "
                    f"available={target_cols}"
                )

        for start in range(0, len(data), chunk_size):
            sub = data.iloc[start : start + chunk_size]
            if sub.empty:
                continue

            sub = sub.where(sub.notna(), None)[target_cols]
            records = sub.to_dict(orient="records")
            if not records:
                continue

            stmt = pg_insert(tbl).values(records)

            if upsert_keys:
                update_cols = {c: stmt.excluded[c] for c in target_cols if c not in upsert_keys}
                if update_cols:
                    stmt = stmt.on_conflict_do_update(index_elements=upsert_keys, set_=update_cols)
                else:
                    stmt = stmt.on_conflict_do_nothing(index_elements=upsert_keys)

            session.execute(stmt)
            total += len(sub)

        session.commit()
        Logger.info(f"Inserted {total} records.")

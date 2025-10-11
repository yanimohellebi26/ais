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


def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    """ Temp normalize function -

    Will be removed in the future, pending other transformation scripts

    """
    df = df.copy()

    for col in ("mmsi", "imo", "vessel_name", "call_sign", "transceiver_class"):
        if col in df.columns:
            df[col] = df[col].astype(str).replace({"nan": None, "<NA>": None, "None": None})

    if "mmsi" in df.columns:
        df = df[df["mmsi"].apply(lambda x: x is not None and len(x) <= 9)]

    for col in ("vessel_type_id", "cargo_type_id"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ("length", "width", "draft"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    if "base_date_time" in df.columns:
        df["base_date_time"] = pd.to_datetime(df["base_date_time"], errors="coerce")

    if "locked" in df.columns:
        df["locked"] = df["locked"].apply(lambda x: bool(int(x)) if pd.notna(x) else False)

    df = df.where(df.notna(), None)
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
        Logger.info("L-Vessels No data to insert.")
        return
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

# etl/etl/load/load_vessel_db.py
import os
from typing import List, Optional, Dict, Iterable

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# --- Chargement de la configuration depuis .env ---
# Essaie d'abord ./.env (racine), sinon tests/.env.exemple
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    dotenv_path = find_dotenv(".env", usecwd=True) or find_dotenv("tests/.env.exemple", usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path)
except Exception:
    # si python-dotenv n'est pas installé, on ignore et on se base sur l'env du système
    pass

# --- Connexion DB via .env / variables d'env ---
PGHOST = os.getenv("DB_HOST", os.getenv("PGHOST", "127.0.0.1"))
PGPORT = int(os.getenv("DB_PORT", os.getenv("PGPORT", "5432")))
PGUSER = os.getenv("DB_USER", os.getenv("PGUSER", "postgres"))
PGPASSWORD = os.getenv("DB_PASSWORD", os.getenv("PGPASSWORD", "postgres"))
PGDATABASE = os.getenv("DB_NAME", os.getenv("PGDATABASE", "ais"))

def _connect():
    return psycopg2.connect(
        host=PGHOST, port=PGPORT, user=PGUSER,
        password=PGPASSWORD, dbname=PGDATABASE
    )

def load_vessel_to_db(
    data: pd.DataFrame,
    *,
    table: str,
    upsert_keys: Optional[List[str]] = None,
    column_mapping: Optional[Dict[str, str]] = None,  # {"df_col": "db_col"}
    chunk_size: int = 10_000
) -> int:
    """
    Insère (ou upsert) un DataFrame `data` dans la table Postgres `table`.
    - table: "schema.table"
    - upsert_keys: colonnes de conflit -> ON CONFLICT DO UPDATE
    - column_mapping: si les noms DF != noms DB (ex: {"MMSI":"mmsi"})
    - chunk_size: taille des batchs d'insertion
    Retourne le nombre total de lignes traitées.
    """
    if data is None or data.empty:
        return 0

    df = data.copy()

    # Harmonise les noms de colonnes vers la DB si nécessaire
    if column_mapping:
        rename_map = {k: v for k, v in column_mapping.items() if k in df.columns}
        if rename_map:
            df = df.rename(columns=rename_map)

    cols: List[str] = list(df.columns)
    cols_sql = ",".join(f'"{c}"' for c in cols)  # protège les noms
    template = "(" + ",".join(["%s"] * len(cols)) + ")"

    # Construire la clause UPSERT si demandé
    if upsert_keys:
        conflict_cols = ",".join(f'"{c}"' for c in upsert_keys)
        set_cols = ",".join(
            f'"{c}" = EXCLUDED."{c}"' for c in cols if c not in upsert_keys
        ) or ""
        upsert_sql = f' ON CONFLICT ({conflict_cols}) DO UPDATE SET {set_cols}' if set_cols else " ON CONFLICT DO NOTHING"
    else:
        upsert_sql = ""

    sql = f'INSERT INTO {table} ({cols_sql}) VALUES %s{upsert_sql}'

    total = 0
    with _connect() as conn:
        with conn.cursor() as cur:
            for start in range(0, len(df), chunk_size):
                sub = df.iloc[start:start + chunk_size]
                # Convertit NaN pandas -> None (NULL Postgres)
                rows = [tuple(None if pd.isna(x) else x for x in r) for r in sub.to_numpy()]
                if not rows:
                    continue
                execute_values(cur, sql, rows, template=template)
                total += len(sub)
        conn.commit()
    return total

# --- Tâche à brancher à la fin du workflow ---
def task_load_vessel_to_db(
    payload,
    *,
    table: str,
    upsert_keys: Optional[List[str]] = None,
    column_mapping: Optional[Dict[str, str]] = None
):
    """
    Tâche pipeline: prend un DataFrame en entrée (payload), insère dans Postgres.
    Retourne un petit récapitulatif.
    """
    if not isinstance(payload, pd.DataFrame):
        raise TypeError("task_load_vessel_to_db attend un pandas.DataFrame en entrée")
    count = load_vessel_to_db(
        payload,
        table=table,
        upsert_keys=upsert_keys,
        column_mapping=column_mapping,
    )
    return {"table": table, "rows_in_df": len(payload), "rows_inserted_or_merged": count}

# --- Test local (exécutable avec: python -m etl.etl.load.load_vessel_db) ---
if __name__ == "__main__":
    # DataFrame de test aligné avec public.vessel
    # - mmsi/imo en texte (varchar dans la table)
    # - call_sign (et pas callsign)
    import pandas as pd

    df = pd.DataFrame({
        "mmsi": ["111111111", "222222222"],      # varchar(9)
        "imo":  ["1234567",   None],             # varchar(7) (None accepté)
        "vessel_name": ["NEPTUNE", "POSEIDON"],
        "call_sign":   ["AAA111",  "BBB222"],    # nom de colonne exact
        # tu peux ajouter d'autres colonnes si tu veux (length, width, ...)
    })

    target_table = "public.vessel"

    # upsert sur la contrainte unique mmsi (elle existe dans ta table)
    try:
        inserted = load_vessel_to_db(
            df,
            table=target_table,
            upsert_keys=["mmsi"]   # correspond à "vessel_mmsi_key"
            # pas besoin de column_mapping: on a déjà call_sign
        )
        print(f"✅ {inserted} lignes insérées/merge dans {target_table}.")
    except Exception as e:
        print(f" Échec insertion: {e}")

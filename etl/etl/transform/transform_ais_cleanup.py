import pandas as pd
import re

from utils.logger import Logger
from utils.timer import timer

@timer
def clean_and_validate_ais(context):
    """
    Nettoyage et validation du DataFrame AIS.
    Affiche le nombre de lignes invalides pour MMSI, IMO, CallSign et dates.
    Utilise Logger et timer pour l'intégration avec le workflow.
    """
    df = context.df

    Logger.info("Début du nettoyage et validation AIS")

    # Nettoyage VesselName et colonnes catégorielles
    df["VesselName"] = df["VesselName"].apply(
        lambda x: re.sub(r"[^A-Za-z0-9 ]", "", str(x).strip().upper()) if pd.notna(x) else None
    )
    for col in ["Cargo", "VesselType", "Status"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    # Bornes physiques
    def check_range(value, min_val, max_val):
        if pd.isna(value) or value < min_val or value > max_val:
            return None
        return value

    df["Length"] = df["Length"].apply(lambda x: check_range(x, 5, 400))
    df["Width"]  = df["Width"].apply(lambda x: check_range(x, 2, 60))
    df["Draft"]  = df["Draft"].apply(lambda x: check_range(x, 0.5, 20))

    # Validation dates
    df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"], errors="coerce")
    Logger.info(f"Dates invalides : {df['BaseDateTime'].isna().sum()}")

    # Vérification identifiants
    Logger.info(f"MMSI invalide : {(~df['MMSI'].astype(str).str.match(r'^\\d{{9}}$')).sum()}")
    Logger.info(f"IMO invalide : {(~df['IMO'].astype(str).str.upper().str.match(r'^IMO\\d{{7}}$')).sum()}")
    Logger.info(f"CallSign invalide : {(~df['CallSign'].astype(str).str.upper().str.match(r'^[A-Z0-9]{3,7}$')).sum()}")

    context.df = df
    Logger.info("Fin du nettoyage et validation AIS")
    return context

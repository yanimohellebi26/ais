# etl/extract/download_range.py
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

from etl.extract.AISDownloader import AISDownloader
from etl.utils.logger import Logger


# Extensions possibles selon les années/sources
POSSIBLE_EXTS = [".csv", ".CSV", ".csv.zst", ".zst", ".zip"]


def _iter_days(start: datetime, end: datetime) -> Iterable[datetime]:
    """Génère chaque jour entre start et end (inclus)."""
    cur = start
    one = timedelta(days=1)
    while cur <= end:
        yield cur
        cur += one


def _expected_stem(day: datetime) -> str:
    """Préfixe de nom attendu (sans extension), ex: AIS_2018_01_01."""
    return f"AIS_{day:%Y_%m_%d}"


def _safe_int_env(name: str, default: int) -> int:
    """Lit une variable d'env en int, sinon renvoie le défaut."""
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


def _find_downloaded_file(base_dir: Path, day: datetime) -> Optional[Path]:
    """
    Cherche un fichier correspondant à la date dans base_dir,
    en testant plusieurs extensions et la casse. Priorise les CSV.
    """
    stem = _expected_stem(day)

    # 1) Essais directs, priorité CSV
    for ext in [".csv", ".CSV", ".csv.zst", ".zst", ".zip"]:
        p = base_dir / f"{stem}{ext}"
        if p.exists():
            return p

    # 2) Fallback: tout ce qui commence par le stem
    matches = sorted(base_dir.glob(f"{stem}*"))
    return matches[0] if matches else None


def download_csv_range(
        start_date: str,
        end_date: str,
        *,
        max_files: Optional[int] = None,  # si None, lit MAX_FILES (env) sinon 50
        skip_existing: bool = True,
        delay_seconds: float = 0.0,
        out_dir: Optional[str] = None,    # si None, utilise AIS_DOWNLOAD_FOLDER ou "."
) -> List[Path]:
    """
    Télécharge les fichiers AIS entre start_date et end_date (inclus).

    Args:
        start_date: 'YYYY-MM-DD'
        end_date: 'YYYY-MM-DD'
        max_files: plafond de sécurité (prioritaire sur env MAX_FILES). Défaut = env MAX_FILES ou 50.
        skip_existing: ne pas retélécharger si un fichier existe déjà pour la date (peu importe l’extension).
        delay_seconds: pause entre téléchargements.
        out_dir: dossier de sortie ; si None, prend AIS_DOWNLOAD_FOLDER (env) ou '.'.

    Returns:
        Liste des chemins des fichiers présents dans le dossier cible.
    """
    # === validation des dates ===
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Format de date invalide. Utilisez 'YYYY-MM-DD YYYY-MM-DD'.")

    if end < start:
        raise ValueError("end_date doit être >= start_date")


    base_dir = Path(out_dir or os.getenv("AIS_DOWNLOAD_FOLDER", "."))
    base_dir.mkdir(parents=True, exist_ok=True)

    # === limite de sécurité ===
    max_allowed = max_files if max_files is not None else _safe_int_env("MAX_FILES", 50)
    Logger.info(f"Limite MAX_FILES = {max_allowed}")

    days = list(_iter_days(start, end))
    if len(days) > max_allowed:
        Logger.warning(f"{len(days)} fichiers demandés, limitation à {max_allowed}.")
        days = days[:max_allowed]

    dl = AISDownloader()
    written: List[Path] = []

    for day in days:
        existing = _find_downloaded_file(base_dir, day)
        if skip_existing and existing:
            Logger.info(f"{existing.name} déjà présent, on saute.")
            written.append(existing)
            continue

        try:
            Logger.info(f"Téléchargement {day:%Y-%m-%d}")
            dl.get_file(day.year, day.month, day.day)

            found = _find_downloaded_file(base_dir, day)

            if not found:
                cwd_found = _find_downloaded_file(Path("."), day)
                if cwd_found:
                    target = base_dir / cwd_found.name
                    if target.resolve() != cwd_found.resolve():
                        target.write_bytes(cwd_found.read_bytes())
                        try:
                            cwd_found.unlink()
                        except Exception:
                            pass
                    found = target

            if found:
                Logger.success(f" {found.name}")
                written.append(found)
            else:
                Logger.error(f" Fichier introuvable après téléchargement: préfixe {_expected_stem(day)}")

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        except Exception as e:
            Logger.error(f" Échec {day:%Y-%m-%d}: {e}")
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    return written

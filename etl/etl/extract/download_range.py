# etl/extract/download_range.py
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

from etl.extract.AISDownloader import AISDownloader
from etl.utils.logger import Logger

POSSIBLE_EXTS = [".csv", ".CSV", ".csv.zst", ".zst", ".zip"]


def _iter_days(start: datetime, end: datetime) -> Iterable[datetime]:
    """Yield each day between start and end (inclusive)."""
    cur = start
    one = timedelta(days=1)
    while cur <= end:
        yield cur
        cur += one


def _expected_stem(day: datetime) -> str:
    """Expected filename prefix (without extension), e.g., AIS_2018_01_01."""
    return f"AIS_{day:%Y_%m_%d}"


def _safe_int_env(name: str, default: int) -> int:
    """Read an int from env, otherwise return default."""
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


def _find_downloaded_file(base_dir: Path, day: datetime) -> Optional[Path]:

    stem = _expected_stem(day)

    for ext in POSSIBLE_EXTS:
        p = base_dir / f"{stem}{ext}"
        if p.exists():
            return p

    matches = sorted(base_dir.glob(f"{stem}*"))
    return matches[0] if matches else None


def download_csv_range(
        start_date: str,
        end_date: str,
        *,
        max_files: Optional[int] = None,
        skip_existing: bool = True,
        delay_seconds: float = 0.0,
        out_dir: Optional[str] = None,
) -> List[Path]:

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Use 'YYYY-MM-DD YYYY-MM-DD'.")

    if end < start:
        raise ValueError("end_date must be >= start_date.")

    base_dir = Path(out_dir or os.getenv("AIS_DOWNLOAD_FOLDER", "."))
    base_dir.mkdir(parents=True, exist_ok=True)

    # --- safety limit ---
    max_allowed = max_files if max_files is not None else _safe_int_env("MAX_FILES", 50)
    Logger.info(f"MAX_FILES limit = {max_allowed}")

    days = list(_iter_days(start, end))
    if len(days) > max_allowed:
        Logger.warning(f"{len(days)} files requested, limiting to {max_allowed}.")
        days = days[:max_allowed]

    dl = AISDownloader()
    written: List[Path] = []

    for day in days:
        existing = _find_downloaded_file(base_dir, day)
        if skip_existing and existing:
            Logger.info(f"{existing.name} already present, skipping.")
            written.append(existing)
            continue

        try:
            Logger.info(f"Downloading {day:%Y-%m-%d}")
            dl.get_file(day.year, day.month, day.day)

            found = _find_downloaded_file(base_dir, day)
            if not found:
                # Sometimes the file lands in CWD; move it if needed
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
                Logger.success(found.name)
                written.append(found)
            else:
                Logger.error(f"File not found after download: prefix {_expected_stem(day)}")

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        except Exception as e:
            Logger.error(f"Failed {day:%Y-%m-%d}: {e}")
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    Logger.success(f"Done. {len(written)} file(s) available in the target directory.")

    return written

import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import date, datetime

from utils.logger import Logger
from etl.extract.FileDownloader import FileDownloader


class AISDownloader(FileDownloader):
    """
    Specialized downloader for AIS files
    """

    COLUMN_MAPPING = {
        "MMSI": "mmsi",
        "mmsi": "mmsi",

        "BaseDateTime": "base_date_time",

        "base_date_time": "base_date_time",
        "LAT": "lat",
        "latitude": "lat",
        "LATITUDE": "lat",

        "LON": "lon",
        "longitude": "lon",
        "LONGITUDE": "lon",

        "SOG": "sog",
        "sog": "sog",

        "COG": "cog",
        "cog": "cog",

        "Heading": "heading",
        "heading": "heading",

        "VesselName": "vessel_name",
        "vessel_name": "vessel_name",

        "IMO": "imo",
        "imo": "imo",

        "CallSign": "call_sign",
        "call_sign": "call_sign",

        "VesselType": "vessel_type_id",
        "vessel_type": "vessel_type_id",
        "vessel_type_id": "vessel_type_id",

        "Status": "status",
        "status": "status",

        "Length": "length",
        "length": "length",
        "Width": "width",
        "width": "width",
        "Draft": "draft",
        "draft": "draft",

        "Cargo": "cargo_type_id",
        "cargo": "cargo_type_id",
        "cargo_type_id": "cargo_type_id",

        "TransceiverClass": "transceiver_class",
        "transceiver": "transceiver_class",
        "transceiver_class": "transceiver_class",
    }

    STANDARD_COLUMNS = [
        "mmsi", "base_date_time", "lon", "lat", "sog", "cog",
        "heading", "vessel_name", "imo", "call_sign", "vessel_type_id",
        "status", "length", "width", "draft", "cargo_type_id", "transceiver_class"
    ]

    def __init__(self, download_folder: str = None):

        base_url = os.getenv("AIS_BASE_URL")

        if download_folder is None:
            download_folder = "data/downloads"

        super().__init__(base_url, download_folder)

    # ----------------------
    # Private methods
    # ----------------------
    @staticmethod
    def _construct_file_name(year: int, target_date: date) -> str:
        if 2015 <= year <= 2024:
            return f"AIS_{year}_{target_date:%m_%d}.zip"
        elif year >= 2025:
            return f"ais-{year}-{target_date:%m-%d}.csv.zst"
        else:
            Logger.error(f"Can't hande file for this year {year}")
            raise ValueError(f"Can't hande file for this year {year}")

    def _get_index_url(self, year: int):
        return f"{self.base_url}/{year}/index.html"

    def _list_files_from_index(self, year: int):
        url = self._get_index_url(year)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except Exception as e:
            Logger.error(f"Can't access {url} : {e}")
            raise ValueError(f"Can't access {url} : {e}")

        soup = BeautifulSoup(r.text, "html.parser")
        files = [a.get("href") for a in soup.find_all("a")
                 if a.get("href") and (a.get("href").endswith(".zip") or a.get("href").endswith(".csv.zst"))]
        return files

    def _normalize_csv(self, csv_path: str) -> str:
        """
        Normalize CSV header in place:
        - Rename columns according to COLUMN_MAPPING
        - Keep original order
        - Check for missing or unknown columns
        """
        with open(csv_path, 'r+', encoding='utf-8') as f:
            header = f.readline().strip()
            original_columns = header.split(',')

            mapped_columns = []
            for col in original_columns:
                if col in self.COLUMN_MAPPING:
                    mapped_columns.append(self.COLUMN_MAPPING[col])
                else:
                    Logger.error(f"Can't handle column {col} in file {csv_path}")
                    raise ValueError(f"Unknown column '{col}' found in file {csv_path}")

            missing_columns = [col for col in self.STANDARD_COLUMNS if col not in mapped_columns]
            if missing_columns:
                Logger.error(f"Missing columns in file {csv_path}: {missing_columns}")
                raise ValueError(f"Missing required columns {missing_columns} in file {csv_path}")

            f.seek(0)
            f.write(','.join(mapped_columns) + '\n')
            f.flush()

        dirname = os.path.dirname(csv_path)
        basename = os.path.basename(csv_path)
        new_basename = basename.replace('-', '_').upper()
        new_path = os.path.join(dirname, new_basename)
        os.rename(csv_path, new_path)

        return new_path

    # ----------------------
    # Publics method
    # ----------------------
    def get_file(self, year: int, month: int, day: int) -> str | None:
        """Download the file, decompress if needed, return path to CSV."""

        try:
            target_date = date(year, month, day)
        except ValueError as e:
            Logger.error(e)
            return None

        file_name = self._construct_file_name(year, target_date)
        csv_name = (file_name
                    .replace(".zip", ".csv")
                    .replace(".csv.zst", ".csv")
                    .replace("-","_"))
        csv_path = os.path.join(self.download_folder, csv_name)

        # If already downloaded (decompressed), skip
        if os.path.exists(csv_path):
            Logger.success(f"File {csv_name} already exists, skipping.")
            return csv_path

        # Check if file exists on server
        available_files = self._list_files_from_index(year)
        if file_name not in available_files:
            Logger.error(f"File {file_name} not found on AIS data provider server")
            raise ValueError(f"File {file_name} not found on AIS data provider server")

        # Download file
        file_path = os.path.join(self.download_folder, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        url = f"{self.base_url}/{year}/{file_name}"
        Logger.info(f"Downloading {file_name} from {url}")

        try:
            resp = requests.get(url)
            resp.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(resp.content)
            Logger.info(f"Downloaded {file_name}")

            # --- Décompression selon le type de fichier ---
            if file_name.endswith(".zip"):
                import zipfile
                with zipfile.ZipFile(file_path, "r") as zf:
                    zf.extractall(os.path.dirname(file_path))
                os.remove(file_path)

            elif file_name.endswith(".zst"):
                import zstandard as zstd
                csv_path = file_path.replace(".csv.zst", ".csv")
                with open(file_path, "rb") as compressed, open(csv_path, "wb") as out:
                    dctx = zstd.ZstdDecompressor()
                    dctx.copy_stream(compressed, out)
                os.remove(file_path)

            else:
                Logger.warning(f"Unknown file type for {file_name}, keeping as is.")
                csv_path = file_path

            csv_path = self._normalize_csv(csv_path)
            return csv_path

        except Exception as e:
            Logger.error(f"Failed to download {file_name}: {e}")
            raise Exception(f"Failed to download {file_name}: {e}")

    def get_size(self, year: int, month: int = None, day: int = None) -> float:
        """Return size of a file (Gb) or total size of year (Gb)"""
        if month is not None and day is not None:
            # Specific file
            target_date = date(year, month, day)
            file_name = self._construct_file_name(year, target_date)
            url = f"{self.base_url}/{year}/{file_name}"
            try:
                r = requests.head(url, allow_redirects=True)
                r.raise_for_status()
                return float(r.headers.get("Content-Length", -1)) / 1e9
            except Exception as e:
                Logger.error(f"Can't get size of {file_name}: {e}")
                return -1

        else:
            # Total size with html parser
            url = f"{self.base_url}/{year}/index.html"
            try:
                r = requests.get(url)
                r.raise_for_status()
                text = r.text
                match = re.search(r'total size.*?([\d.]+)\s*GB', text, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                else:
                    Logger.warning(f"Total size not found in index page for {year}")
                    return -1
            except Exception as e:
                Logger.error(f"Can't access {url} : {e}")
                return -1

    def get_file_list(self, year: int, month: int = None):
        """Return list of files for year or year+month"""
        files = self._list_files_from_index(year)
        if month is None:
            return files
        month_str = f"_{month:02d}_"
        return [f for f in files if month_str in f]

    def get_latest_file_available(self):
        """Download last AIS file available"""

        current_year = date.today().year
        file_list = self.get_file_list(current_year)

        if not file_list:
            Logger.error(f"No file available for {current_year}")
            return None

        dates = []
        for f in file_list:
            match = re.search(r'\d{4}-\d{2}-\d{2}', f)
            if match:
                try:
                    d = datetime.strptime(match.group(), "%Y-%m-%d").date()
                    dates.append((d, f))
                except ValueError:
                    pass

        if not dates:
            Logger.error(f"No date found for files in {current_year}")
            return None

        latest_date, latest_file = max(dates, key=lambda x: x[0])

        return self.get_file(latest_date.year, latest_date.month, latest_date.day)




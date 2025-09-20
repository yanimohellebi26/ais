import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import date, datetime
import configparser
from etl.utils.logger import Logger
from etl.utils.FileDownloader import FileDownloader


class AISDownloader(FileDownloader):
    """
    Specialized downloader for AIS files
    """

    def __init__(self, download_folder: str = None):
        cfg = configparser.ConfigParser()
        cfg.read("config.ini")
        base_url = cfg["AIS"]["base_url"]

        if download_folder is None:
            download_folder = cfg.get("AIS", "download_folder", fallback="data/local/downloads")

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
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        files = [a.get("href") for a in soup.find_all("a")
                 if a.get("href") and (a.get("href").endswith(".zip") or a.get("href").endswith(".csv.zst"))]
        return files

    # ----------------------
    # Publics method
    # ----------------------
    def get_file(self, year: int, month: int, day: int) -> str | None:
        """Download the file, unzip, return path to CSV. Keep only CSV."""

        target_date = date(year, month, day)
        zip_name = self._construct_file_name(year, target_date)
        csv_name = zip_name.replace(".zip", ".csv")  # nom final CSV
        csv_path = os.path.join(self.download_folder, csv_name)

        # If csv already exists, return file path
        if os.path.exists(csv_path):
            return csv_path

        # Check zip available on server
        available_files = self._list_files_from_index(year)
        if zip_name not in available_files:
            Logger.error(f"File {zip_name} not found on server")
            return None

        # Download ZIP
        zip_path = os.path.join(self.download_folder, zip_name)
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        url = f"{self.base_url}/{year}/{zip_name}"
        Logger.info(f"Downloading {zip_name} from {url}")
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            with open(zip_path, "wb") as f:
                f.write(resp.content)
            Logger.success(f"Downloaded {zip_name}")

            # Unzip
            import zipfile
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(os.path.dirname(zip_path))

            # Remove zip, keep only csv
            os.remove(zip_path)

            return csv_path

        except Exception as e:
            Logger.error(f"Failed to download {zip_name}: {e}")
            return None

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

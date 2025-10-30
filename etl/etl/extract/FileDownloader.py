import requests
import os
from utils.logger import Logger
class FileDownloader:
    """
    Downloader file from website
    """

    def __init__(self, base_url, download_folder="downloads"):
        """
        :param base_url: root URL of website
        :param download_folder: Dossier où seront stockés les fichiers téléchargés
        """
        self.base_url = base_url
        self.download_folder = download_folder

        if not os.path.exists(download_folder):
            os.makedirs(download_folder)


    def _construct_file_url(self, file_name):
        return f"{self.base_url}/{file_name}"


    def download_file(self, file_name):
        """
        Download specific file
        """
        url = self._construct_file_url(file_name)
        file_path = os.path.join(self.download_folder, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        Logger.info(f"Try downloaded {file_name} from {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(response.content)
            Logger.success(f"Downloaded {file_name}")
        except requests.HTTPError as e:
            Logger.error(f"Downloading {file_name}, URL : {url}, Error: {e.response.status_code}")
        except Exception as e:
            Logger.error(f"Exception {file_name}, URL : {url}, Error: {e}")

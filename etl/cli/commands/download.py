import click
import os
from dotenv import load_dotenv

from cli.commands.TaskPublisher import TaskPublisher
from etl.extract.AISDownloader import AISDownloader
from utils.logger import Logger

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

@click.command(name="download")
@click.option("--date", "-d", help="Date format YYYY-MM-DD")
@click.option("--latest", is_flag=True, help="Download latest available file")
def download_cmd(date, latest, publisher=None):
    """Download AIS file for a given date"""
    if publisher is None:
        publisher = TaskPublisher(dummy=True)

    Logger.info("Run Download")

    try:
        downloader = AISDownloader()
        csv_path = downloader.get_latest_file_available() if latest else downloader.get_file(*map(int, date.split("-")))
        if not csv_path:
            publisher.log(f"No file download", "error")
            raise ValueError("No file downloaded")

        publisher.log(f"Download ${csv_path}", "success")

        Logger.success(f"File ready: {csv_path}")

    except Exception as e:
        publisher.log(f"Download failed","error")
        Logger.error(f"Download failed: {e}")
        raise Exception(f"Download failed: {e}")

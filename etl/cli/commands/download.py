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
@click.option("--range", "-r", "range_dates", nargs=2, help="Date range (start end) as YYYY-MM-DD YYYY-MM-DD")
def download_cmd(date, latest, range_dates, publisher=None):
    """Download AIS files"""
    if publisher is None:
        publisher = TaskPublisher(dummy=True)

    modes = [bool(date), bool(latest), bool(range_dates)]

    if sum(modes) != 1:
        Logger.error("Specify exactly one mode: --date | --latest | --range <start end>.")
        return

    Logger.info("Run Download")

    try:
        downloader = AISDownloader(publisher)

        if date:
            downloader.get_file(*map(int, date.split("-")))

        elif range_dates:
            start_s, end_s = range_dates
            downloader.download_range(start_s, end_s)
        elif latest:
            downloader.get_latest_file_available()
        else :
            Logger.error("No options provided.")

        publisher.log(f"Download", "success")
        Logger.success(f"File(s) ready")

    except Exception as e:
        publisher.log(f"Download failed","error")
        Logger.error(f"Download failed: {e}")
        raise Exception(f"Download failed: {e}")

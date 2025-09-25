from etl.extract.AISDownloader import AISDownloader
from dotenv import load_dotenv
from etl.utils.logger import Logger
import click

load_dotenv()

@click.group()
def cli():
    pass

@cli.command()
@click.option("--date","-d",help="Date to format YYYY-MM-DD")
def download(date):
    """Télécharger un fichier pour une date donnée"""
    Logger.info(f"Run task download")
    y,m,d = map(int,date.split("-"))
    downloader = AISDownloader()
    downloader.get_file(y,m,d)
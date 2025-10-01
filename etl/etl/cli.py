from etl.extract.AISDownloader import AISDownloader
from dotenv import load_dotenv

import etl.transform.transform_vessel_delta as dv
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

@cli.command()
def test():
    Logger.info("Run test")
    dv.clear_vessels_db()
    dv.insert_test_data()
    df_vessels = dv.get_vessels_db()
    print(df_vessels.head())

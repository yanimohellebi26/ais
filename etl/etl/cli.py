import pandas as pd

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
def load_vessels():
    Logger.info("Run task load vessels")
    rename_map = {
        "MMSI": "mmsi",
        "BaseDateTime": "last_update",
        "VesselName": "vessel_name",
        "IMO": "imo",
        "CallSign": "call_sign",
        "VesselType": "vessel_type_id",
        "Length": "length",
        "Width": "width",
        "Draft": "draft",
        "Cargo": "cargo_type_id",
        "TransceiverClass": "transceiver_class",
    }
    new_data = pd.read_csv("data/share/tests/test_vessels_new.csv")
    new_data.rename(columns=rename_map,inplace=True)
    new_data = new_data[list(rename_map.values())]

    # Transform : Delta detection
    old_data = dv.get_vessels_db()
    res = dv.transform_vessel_delta(new_data,old_data)

    print(res)

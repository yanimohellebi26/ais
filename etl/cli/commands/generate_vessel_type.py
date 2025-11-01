import click
import pandas as pd
from etl.load.generate_vessel_type import load_vessel_type
from utils.logger import Logger

@click.command(name="generate-vessel-type")
@click.option("--file", "-f", required=True, help="CSV file path")
@click.option("--output-file", "-o", help="Output SQL file path")
def generate_vessel_type_cmd(file, output_file):
    """Generate vessel type SQL migration"""
    Logger.info("Run generate vessel type")
    data = pd.read_csv(file, sep=';')
    load_vessel_type(data, output_file)
    Logger.success(f"File generated: {output_file}")

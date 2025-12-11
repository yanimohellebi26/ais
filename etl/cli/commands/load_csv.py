import click
import os
from dotenv import load_dotenv

from cli.commands.TaskPublisher import TaskPublisher
from utils.logger import Logger
from etl.load.load_csv_to_db import load_csv_to_db

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

@click.command(name="load_csv")
@click.option("--file", "-f", required=True, help="CSV file to load")
@click.option("--table", "-t", required=True, help="Database table name")
def load_csv_cmd(file, table, publisher = None):
    """
    Load CSV file into the specified database table.
    CSV file must have a format corresponding to table DDL
    """
    if publisher is None:
        publisher = TaskPublisher(dummy=True)

    if not os.path.exists(f"data/downloads/{file}"):
        Logger.error(f"File does not exist: data/downloads/{file}")
        raise FileNotFoundError(f"File not found: data/downloads/{file}")

    Logger.info(f"Starting to load CSV '{file}' into table '{table}'...")
    publisher.log(f"Starting to load CSV '{file}' into table '{table}'...","running")
    try:
        load_csv_to_db(csv_file=f"data/downloads/{file}", table_name=table)
        Logger.success(f"CSV '{file}' successfully loaded into table '{table}'.")
    except Exception as e:
        Logger.error(f"Failed to load CSV: {e}")
        raise

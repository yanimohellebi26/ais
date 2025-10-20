import os
import time
import uuid

import click
import pandas as pd
from dotenv import load_dotenv

from etl.extract.AISDownloader import AISDownloader
from etl.extract.extract_ais import extract_data_from_file
from etl.load.generate_vessel_type import load_vessel_type
from etl.transform.transform_ais_downsampling import downsample_ais
from etl.transform.transform_general_ais import remove_rows_with_empty, remove_rows_with_wrong_format, normalize_ais
from etl.transform.transform_vessel_duplication import clean_vessel_duplication
from etl.transform.transform_vessel_delta import transform_vessel_delta, get_vessels_db
from etl.load.load_vessel_db import load_vessel_to_db
from etl.utils.logger import Logger
from etl.utils.timer import timer

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


@click.group()
def cli():
    pass

#
# ===== CLI COMMANDS =====
#

@cli.command()
def hello():
    print("hello")

@cli.command()
@click.option("--date", "-d", help="Date to format YYYY-MM-DD")
@click.option("--latest", is_flag=True, help="Download latest file available")
def download(date, latest):
    """Download file for a given date"""
    Logger.info(f"Run task download")
    downloader = AISDownloader()
    if latest:
        downloader.get_latest_file_available()
    else :
        y, m, d = map(int, date.split("-"))
        downloader.get_file(y, m, d)

@cli.command()
@click.option("--file", "-f", help="File path to csv")
@click.option("--output-file", "-o", help="Output file path for SQL")
def generate_vessel_type(file, output_file):
    """Generate vessel type migration sql"""
    Logger.info(f"Run task generate_vessel_type")
    data = pd.read_csv(file,sep = ';')
    if output_file is None:
        load_vessel_type(data)
    else:
        load_vessel_type(data, output_file)
#
# ===== WORKFLOWS / PIPELINES =====
#

# === Workflows defs ===
PIPELINES = {
    "load-vessels": [
        (extract_data_from_file, {"selected_map": [ "mmsi", "base_date_time", "vessel_name", "imo", "call_sign",
        "vessel_type_id", "length", "width", "draft", "cargo_type_id","transceiver_class",]}),
        (normalize_ais, {}),
        (remove_rows_with_empty, {"required": ["mmsi", "base_date_time"]}),
        (remove_rows_with_wrong_format, {}),
        (clean_vessel_duplication, {}),
        (get_vessels_db, {}),
        (transform_vessel_delta, {}),
        (load_vessel_to_db,{"table":"vessel", "upsert_keys": ["mmsi"] })
    ],
    "load-positions": [
        (extract_data_from_file,{"selected_map": [ "mmsi", "base_date_time", "lon","lat","sog","cog","heading"]}),
        (downsample_ais,{}),
        (normalize_ais, {}),
        (remove_rows_with_wrong_format, {}),
    ]
}


@cli.command()
@click.option("--pipeline", "-p", required=True, help="Pipeline name (ex: load_vessels, monthly)")
@click.option("--file", "-f", help="File path (ex: ./data/file.csv)")
@click.option("--fail-fast", "-ff", is_flag=True, help="Stop pipeline on first error (by default)")
@click.option("--continue-on-error", "-coe", is_flag=True, help="Continue pipeline to next call function")
@click.option("--use-timer", "-t", is_flag=True, help="Measure execution time for each task")
@click.option("--workflow-name", "-n", type=str, help="Optional name for this pipeline run")
def run_pipeline(pipeline, file, fail_fast, continue_on_error, use_timer, workflow_name):
    tasks = PIPELINES.get(pipeline)
    if not tasks:
        Logger.error(f"Pipeline '{pipeline}' not found. Options: {list(PIPELINES.keys())}")
        return

    workflow_id = workflow_name or str(uuid.uuid4())[:8]

    from etl.models.context import VesselContext

    context: VesselContext = VesselContext(
        file=file,
        workflow_id=workflow_id,
    )

    Logger.info(f"[W-{workflow_id}] Start pipeline '{pipeline}'")
    workflow_start = time.time()

    for func, kwargs in tasks:
        try:
            if use_timer:
                timed_func = timer(func)
                context = timed_func(context, **kwargs)
            else:
                context = func(context, **kwargs)
        except Exception as e:
            Logger.error(f"[W-{workflow_id}] Error in '{func.__name__}' : {e}")
            if continue_on_error:
                continue
            else:
                Logger.error(f"[W-{workflow_id}] Pipeline '{pipeline}' fail fast stop")
                break

    Logger.success(
        f"[W-{workflow_id}] Pipeline '{pipeline}' finished successfully in {time.time() - workflow_start:.2f}s")

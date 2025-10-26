import json
import os
import time

import click
import pandas as pd
from dotenv import load_dotenv

from etl.extract.AISDownloader import AISDownloader
from etl.load.generate_vessel_type import load_vessel_type
from etl.utils import task_store
from etl.utils.loader import load_pipelines
from etl.utils.logger import Logger
from etl.utils.timer import timer

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

@click.group()
def cli():
    pass


@cli.command()
@click.option("--time-sleep", "-t", help="Time to sleep in seconds", default=10, type=int)
def hello(time_sleep,task_id=None):
    Logger.info(f"Hello World")
    time.sleep(time_sleep)
    return {"status":"success"}


@cli.command()
@click.option("--date", "-d", help="Date to format YYYY-MM-DD")
@click.option("--latest", is_flag=True, help="Download latest file available")
def download(date, latest,task_id=None):
    """Download file for a given date"""
    Logger.info(f"Run task download")
    try:
        downloader = AISDownloader()
        if latest:
            csv_path = downloader.get_latest_file_available()
        else:
            y, m, d = map(int, date.split("-"))
            csv_path = downloader.get_file(y, m, d)

        if not csv_path:
            raise ValueError('No file downloaded')

        Logger.success(f"File ready: {csv_path}")
        return {"file": csv_path, "status": "success"}
    except Exception as e:
        Logger.error(f"Download failed: {e}")
        return {"status": "error", "error": str(e)}


@cli.command()
@click.option("--file", "-f", help="File path to csv", required=True)
@click.option("--output-file", "-o", help="Output file path for SQL", required=True)
def generate_vessel_type(file, output_file,task_id=None):
    """Generate vessel type migration sql"""
    Logger.info(f"Run task generate_vessel_type")
    data = pd.read_csv(file,sep = ';')
    if output_file is None:
        load_vessel_type(data)
    else:
        load_vessel_type(data, output_file)


@cli.command()
@click.option("--pipeline", "-p", required=True, help="Pipeline name (ex: load_vessels, monthly)")
@click.option("--file", "-f", help="File path (ex: ./data/file.csv)")
@click.option("--fail-fast", "-ff", is_flag=True, default=True, help="Stop pipeline on first error (by default)")
@click.option("--continue-on-error", "-coe", is_flag=True, help="Continue pipeline to next call function")
@click.option("--use-timer", "-t", is_flag=True, help="Measure execution time for each task")
@click.option("--extra-kwargs", required=False, help="Dynamic kwargs for pipeline functions")
def run_pipeline(pipeline, file, fail_fast, continue_on_error, use_timer,extra_kwargs, task_id=None):
    result = {"status": "success", "details": []}
    print(task_id)
    # Convert kwargs for pipeline
    if extra_kwargs:
        if isinstance(extra_kwargs, str): # for CLI calls
            try:
                extra_kwargs = json.loads(extra_kwargs)
            except json.JSONDecodeError:
                Logger.error("Invalid JSON format for --extra-kwargs")
                result["status"] = "error"
                result["error"] = f"Invalid JSON format for --extra-kwargs"
                return result
        elif isinstance(extra_kwargs, dict):  # for API calls
            pass
        else:
            Logger.error(f"Invalid type for extra_kwargs: {type(extra_kwargs)}")
            result["status"] = "error"
            result["error"] = f"Invalid type for extra_kwargs: {type(extra_kwargs)}"
            return result
    else:
        extra_kwargs = {}

    all_pipelines = load_pipelines(extra_kwargs)
    tasks = all_pipelines.get(pipeline)

    if not tasks:
        Logger.error(f"Pipeline '{pipeline}' not found.")
        result["status"] = "error"
        result["error"] = f"Pipeline '{pipeline}' not found."
        return result

    from etl.models.context import PipelineContext

    context: PipelineContext = PipelineContext(file=file)

    Logger.info(f"Start pipeline '{pipeline}'")
    workflow_start = time.time()

    for func, kwargs in tasks:
        try:
            if use_timer:
                timed_func = timer(func)
                context = timed_func(context, **kwargs)
            else:
                context = func(context, **kwargs)

            if task_id is not None:
                task_store.set_task_meta(task_id, {
                    **task_store.get_task_meta(task_id),
                    "last_step": func.__name__,
                    "step_status": "success",
                })

            result["details"].append({"task": func.__name__, "status": "success"})
        except Exception as e:
            if task_id is not None:
                task_store.set_task_meta(task_id, {
                    **task_store.get_task_meta(task_id),
                    "last_step": func.__name__,
                    "step_status": "error",
                    "step_error": str(e)
                })

            Logger.error(f"Error in '{func.__name__}' : {e}")
            result["details"].append({"task": func.__name__, "status": "error", "error": str(e)})
            if fail_fast:
                Logger.error(f"Pipeline '{pipeline}' fail fast stop")
                break
            elif continue_on_error:
                continue
            else:
                Logger.error(f"Pipeline '{pipeline}' fail fast stop")
                break

    Logger.success(
        f"Pipeline '{pipeline}' finished successfully in {time.time() - workflow_start:.2f}s")
    return result


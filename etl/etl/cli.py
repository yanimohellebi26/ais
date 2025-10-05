import time
import uuid

import click
from dotenv import load_dotenv

from etl.extract.AISDownloader import AISDownloader
from etl.extract.extract_vessels import extract_vessels
from etl.transform.transform_vessel_duplication import clean_vessel_duplication
from etl.transform.transform_vessel_delta import transform_vessel_delta, get_vessels_db
from etl.utils.logger import Logger
from etl.utils.timer import timer

load_dotenv()


@click.group()
def cli():
    pass

#
# ===== CLI COMMANDS =====
#

@cli.command()
@click.option("--date", "-d", help="Date to format YYYY-MM-DD")
def download(date):
    """Télécharger un fichier pour une date donnée"""
    Logger.info(f"Run task download")
    y, m, d = map(int, date.split("-"))
    downloader = AISDownloader()
    downloader.get_file(y, m, d)


#
# ===== WORKFLOWS / PIPELINES =====
#

# === Workflows defs ===
WORKFLOWS = {
    "load-vessels": [
        (extract_vessels, {}),
        (clean_vessel_duplication, {}),
        (get_vessels_db, {}),
        (transform_vessel_delta, {})
    ]
}


@cli.command()
@click.option("--workflow", "-w", required=True, help="Workflow name (ex: load_vessels, monthly)")
@click.option("--file", "-f", help="File path (ex: ./data/file.csv)")
@click.option("--fail-fast", "-ff", is_flag=True, help="Stop workflow on first error (by default)")
@click.option("--continue-on-error", "-coe", is_flag=True, help="Continue workflow to next call function")
@click.option("--use-timer", "-t", is_flag=True, help="Measure execution time for each task")
@click.option("--workflow-name", "-n", type=str, help="Optional name for this workflow run")
def run(workflow, file, fail_fast, continue_on_error, use_timer, workflow_name):
    tasks = WORKFLOWS.get(workflow)
    if not tasks:
        Logger.error(f"Workflow '{workflow}' not found. Options: {list(WORKFLOWS.keys())}")
        return

    workflow_id = workflow_name or str(uuid.uuid4())[:8]

    from etl.models.context import VesselContext

    context: VesselContext = VesselContext(
        file=file,
        workflow_id=workflow_id,
    )

    Logger.info(f"[W-{workflow_id}] Start workflow '{workflow}'")
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
                Logger.error(f"[W-{workflow_id}] Workflow '{workflow}' fail fast stop")
                break

    Logger.success(
        f"[W-{workflow_id}] Workflow '{workflow}' finished successfully in {time.time() - workflow_start:.2f}s")

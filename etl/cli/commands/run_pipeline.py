import click
from etl.runner import run
from utils.logger import Logger

@click.command(name="run-pipeline")
@click.option("--pipeline", "-p", required=True, help="Pipeline name (ex: load_vessels)")
@click.option("--file", "-f", help="Path to input file")
@click.option("--continue-on-error", "-coe", is_flag=True, help="Continue to next task on error")
@click.option("--use-timer", "-t", is_flag=True, help="Measure execution time for each task")
def run_pipeline_cmd(pipeline, file, continue_on_error, use_timer):
    """Run a specific ETL pipeline"""
    Logger.info(f"Run pipeline: {pipeline}")
    run(pipeline, file, continue_on_error, use_timer)

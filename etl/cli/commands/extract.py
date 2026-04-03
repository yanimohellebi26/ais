import click
import os

from etl.extract.Decompresser import decompress_WDPA_zip

from etl.models.context import PipelineContext
from cli.commands.TaskPublisher import TaskPublisher
from utils.logger import Logger

@click.command(name="extract-wdpa")
@click.option("--file", "-f", required=True, help="WDPA .zip file name ")
def extract_wdpa_cmd(file, publisher=None):
    """Extract WDPA .zip file"""
    if publisher is None:
        publisher = TaskPublisher(dummy=True)

    Logger.info(f"Run Extract WDPA on {file}")

    try:
        context = PipelineContext(file=file)
        decompress_WDPA_zip(context)

        publisher.log(f"Extract WDPA", "success")
        Logger.success(f"File(s) ready")

    except Exception as e:
        publisher.log(f"Extract WDPA failed","error")
        Logger.error(f"Extract WDPA failed: {e}")
        raise Exception(f"Extract WDPA failed: {e}")
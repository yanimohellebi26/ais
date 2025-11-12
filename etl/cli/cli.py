import click

from cli.commands.clean import clean_cmd
from cli.commands.download import download_cmd
from cli.commands.generate_vessel_type import generate_vessel_type_cmd
from cli.commands.hello import hello_cmd
from cli.commands.load_csv import load_csv_cmd
from cli.commands.run_pipeline import run_pipeline_cmd


@click.group()
def cli():
    """ETL Command Line Interface"""
    pass

# Add commands
cli.add_command(hello_cmd)
cli.add_command(download_cmd)
cli.add_command(generate_vessel_type_cmd)
cli.add_command(run_pipeline_cmd)
cli.add_command(clean_cmd)
cli.add_command(load_csv_cmd)
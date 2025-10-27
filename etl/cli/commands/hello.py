import time
import click
from cli.commands.TaskPublisher import TaskPublisher
from utils.logger import Logger


@click.command(name="hello")
@click.option("--time-sleep", "-t", default=10, type=int, help="Time to sleep in seconds")
def hello_cmd(time_sleep,publisher=None):
    """Simple test command"""
    if publisher is None:
        publisher = TaskPublisher(dummy=True)

    publisher.log("Run Hello World")
    time.sleep(time_sleep)
    publisher.log("Done sleeping", level="success")
    return {"message": f"Hello World after {time_sleep} seconds"}

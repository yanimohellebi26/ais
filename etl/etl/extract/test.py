from time import sleep

from etl.models.context import PipelineContext


def test(context: PipelineContext, timer = 2):
    sleep(timer)

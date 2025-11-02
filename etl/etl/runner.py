import time

from utils.logger import Logger
from utils.timer import timer
from etl.loader import load_pipelines

def run(pipeline, file, continue_on_error=False, use_timer=True):
    """
    Run pipeline
    Args:
        pipeline: pipeline name defined in config yaml file
        file: data file source
        fail_fast: if true, stop execution after failure
        continue_on_error: if true, continue execution after failure
        use_timer: time every step of the pipeline
    """
    all_pipelines = load_pipelines()
    tasks = all_pipelines.get(pipeline)

    if not tasks:
        Logger.error(f"Pipeline '{pipeline}' not found.")
        return

    from etl.models.context import PipelineContext

    context: PipelineContext = PipelineContext(file=file)

    Logger.info(f"Start pipeline '{pipeline}'")
    workflow_start = time.time()

    for func, kwargs in tasks['steps']:
        try:
            if use_timer:
                timed_func = timer(func)
                context = timed_func(context, **kwargs)
            else:
                context = func(context, **kwargs)

        except Exception as e:
            Logger.error(f"Error in '{func.__name__}' : {e}")
            if continue_on_error:
                continue
            else:
                Logger.error(f"Pipeline '{pipeline}' fail fast stop")
                break

    Logger.success(
        f"Pipeline '{pipeline}' finished successfully in {time.time() - workflow_start:.2f}s")
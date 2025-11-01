import time
from datetime import datetime

from etl.loader import load_pipelines
from utils.timer import timer
from worker.celery_app import celery_app


@celery_app.task(bind=True, name="run_pipeline")
def run_task_pipeline(
    self,
    pipeline,
    file,
    extra_kwargs,
    continue_on_error=False,
    use_timer=True,
    user=None
):
    from worker.store import TaskStore

    task_id = self.request.id
    now = datetime.utcnow().isoformat()

    # --- Init METADATA --- #
    TaskStore.set_meta(task_id, {
        "task_id": task_id,
        "command": "run-pipeline",
        "pipeline": pipeline,
        "file": file,
        "kwargs": extra_kwargs,
        "user": user,
        "status": "queued",
        "created_at": now,
        "started_at": None,
        "ended_at": None
    })

    # --- PIPELINE QUEUED --- #
    TaskStore.append_log(task_id, "pipeline", "queued", {"pipeline": pipeline})

    # --- Start pipeline --- #
    meta = TaskStore.get_meta(task_id)
    meta["status"] = "running"
    meta["started_at"] = datetime.utcnow().isoformat()
    TaskStore.set_meta(task_id, meta)

    # --- Load pipelines --- #
    all_pipelines = load_pipelines(extra_kwargs)
    tasks = all_pipelines.get(pipeline)
    if not tasks:
        error_msg = f"Pipeline '{pipeline}' not found."
        TaskStore.append_log(task_id, "pipeline", "error", {"pipeline": pipeline, "error": error_msg})
        meta["status"] = "error"
        meta["ended_at"] = datetime.utcnow().isoformat()
        TaskStore.set_meta(task_id, meta)
        return

    from etl.models.context import PipelineContext
    context = PipelineContext(file=file)

    workflow_start = time.time()

    TaskStore.append_log(task_id, "pipeline", "running", {"pipeline": pipeline,"steps_count": len(tasks["steps"])})

    count = 0
    for func, kwargs in tasks["steps"]:
        count += 1
        step_name = func.__name__

        # --- STEP RUNNING --- #
        TaskStore.append_log(task_id, "step", "running", {"index": count, "step": step_name})

        try:
            if use_timer:
                timed_func = timer(func)
                context = timed_func(context, **kwargs)
            else:
                context = func(context, **kwargs)

            # --- STEP SUCCESS --- #
            TaskStore.append_log(task_id, "step", "success", {"index": count, "step": step_name})

        except Exception as e:
            error_msg = str(e)
            TaskStore.append_log(task_id, "step", "error", {"index": count, "step": step_name, "error": error_msg})

            if continue_on_error:
                TaskStore.append_log(task_id, "pipeline", "warning", {"pipeline": pipeline, "message": "Error ignored, continuing pipeline"})
                continue
            else:
                TaskStore.append_log(task_id, "pipeline", "error", {"pipeline": pipeline, "message": "Pipeline stopped (fail fast)"})
                meta["status"] = "error"
                TaskStore.set_meta(task_id, meta)
                return


    duration = time.time() - workflow_start
    TaskStore.append_log(task_id, "pipeline", "success", {
        "pipeline": pipeline,
        "duration": f"{duration:.2f}s",
        "message": "Pipeline executed successfully"})

    # --- Finalize --- #
    meta["ended_at"] = datetime.utcnow().isoformat()
    meta["status"] = "success"
    TaskStore.set_meta(task_id, meta)

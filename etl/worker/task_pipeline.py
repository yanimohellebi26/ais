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
        "ended_at": None,
        "result": None,
        "error": None,
        "last_step": None,
        "step_status": None,
    })

    TaskStore.append_log(task_id, f"Pipeline '{pipeline}' queued.")

    # --- Update status -> running --- #
    meta = TaskStore.get_meta(task_id)
    meta["status"] = "running"
    meta["started_at"] = datetime.utcnow().isoformat()
    TaskStore.set_meta(task_id, meta)
    TaskStore.append_log(task_id, f"Pipeline '{pipeline}' démarré.")

    # --- Load pipelines --- #
    all_pipelines = load_pipelines(extra_kwargs)
    tasks = all_pipelines.get(pipeline)
    if not tasks:
        error_msg = f"Pipeline '{pipeline}' introuvable."
        TaskStore.append_log(task_id, error_msg, level="error")
        meta["status"] = "error"
        meta["error"] = error_msg
        meta["ended_at"] = datetime.utcnow().isoformat()
        TaskStore.set_meta(task_id, meta)
        return

    from etl.models.context import PipelineContext
    context = PipelineContext(file=file)

    workflow_start = time.time()
    result = {"details": []}

    TaskStore.append_log(task_id, f"Pipeline '{pipeline}' has {len(tasks)} steps")

    # --- Pipeline steps --- #
    for func, kwargs in tasks:
        step_name = func.__name__
        TaskStore.append_log(task_id, f"Step '{step_name}' running")
        meta["last_step"] = step_name
        TaskStore.set_meta(task_id, meta)

        try:
            # Execute + timer
            if use_timer:
                timed_func = timer(func)
                context = timed_func(context, **kwargs)
            else:
                context = func(context, **kwargs)

            TaskStore.append_log(task_id, f"Step '{step_name}' success")
            meta["step_status"] = "success"
            TaskStore.set_meta(task_id, meta)
            result["details"].append({"task": step_name, "status": "success"})

        except Exception as e:
            error_msg = f"Erreur dans '{step_name}': {e}"
            TaskStore.append_log(task_id, error_msg, level="error")
            meta["step_status"] = "error"
            meta["step_error"] = str(e)
            TaskStore.set_meta(task_id, meta)
            result["details"].append({"task": step_name, "status": "error", "error": str(e)})

            if continue_on_error:
                TaskStore.append_log(task_id, f"Error ignored, continue pipeline")
                continue
            else:
                TaskStore.append_log(task_id, f"Pipeline stop (fail fast)", level="error")
                break

    duration = time.time() - workflow_start
    TaskStore.append_log(task_id, f"Pipeline '{pipeline}' stop in {duration:.2f}s")

    # --- End --- #
    meta = TaskStore.get_meta(task_id)
    meta["ended_at"] = datetime.utcnow().isoformat()
    if any(d["status"] == "error" for d in result["details"]):
        meta["status"] = "error"
        TaskStore.append_log(task_id, f"Pipeline '{pipeline}' end with errors", level="error")
    else:
        meta["status"] = "success"
        TaskStore.append_log(task_id, f"Pipeline '{pipeline}' execute with success")
    meta["result"] = result
    TaskStore.set_meta(task_id, meta)

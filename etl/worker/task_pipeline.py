import time
from datetime import datetime
from sqlalchemy import text

from etl.loader import load_pipelines
from utils.timer import timer
from worker.celery_app import celery_app
from utils.db import get_session

import os

from worker.pipeline_history_db import PipelineHistoryDB

if os.getenv("ENV_MODE") == "local":
    if os.path.exists("/.dockerenv") or os.getenv("RUNNING_IN_DOCKER") == "1":
        os.environ["ENV_MODE"] = "docker"
        os.environ["DB_HOST"] = "ais-db"


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

    TaskStore.append_log(task_id, "pipeline", "queued", {"pipeline": pipeline})

    PipelineHistoryDB.insert_history_running(pipeline_name=pipeline,file=file)

    # --- Start pipeline --- #
    meta = TaskStore.get_meta(task_id)
    meta["status"] = "running"
    meta["started_at"] = datetime.utcnow().isoformat()
    TaskStore.set_meta(task_id, meta)

    all_pipelines = load_pipelines(extra_kwargs)
    tasks = all_pipelines.get(pipeline)
    if not tasks:
        error_msg = f"Pipeline '{pipeline}' not found."
        TaskStore.append_log(task_id, "pipeline", "error", {"pipeline": pipeline, "error": error_msg})
        meta["status"] = "error"
        meta["ended_at"] = datetime.utcnow().isoformat()
        TaskStore.set_meta(task_id, meta)

        PipelineHistoryDB.delete_registry_entry(pipeline, file)


    from etl.models.context import PipelineContext
    context = PipelineContext(file=file)
    workflow_start = time.time()

    TaskStore.append_log(task_id, "pipeline", "running", {"pipeline": pipeline,"steps_count": len(tasks["steps"])})
    count = 0

    try:
        for func, kwargs in tasks["steps"]:
            count += 1
            step_name = func.__name__
            TaskStore.append_log(task_id, "step", "running", {"index": count, "step": step_name})

            if use_timer:
                timed_func = timer(func)
                context = timed_func(context, **kwargs)
            else:
                context = func(context, **kwargs)

            TaskStore.append_log(task_id, "step", "success", {"index": count, "step": step_name})

        duration = time.time() - workflow_start
        TaskStore.append_log(task_id, "pipeline", "success", {
            "pipeline": pipeline,
            "duration": f"{duration:.2f}s",
            "message": "Pipeline executed successfully"
        })

        meta["ended_at"] = datetime.utcnow().isoformat()
        meta["status"] = "success"
        TaskStore.set_meta(task_id, meta)

        with get_session() as session:
            session.execute(
                text("""
                    UPDATE pipeline_file_registry
                    SET status='success', ended_at=NOW()
                    WHERE pipeline_name=:p AND file_name=:f
                """),
                {"p": pipeline, "f": file}
            )
            session.commit()

    except Exception as e:
        error_msg = str(e)
        TaskStore.append_log(task_id, "step", "error", {"index": count, "error": error_msg})

        meta["status"] = "error"
        meta["ended_at"] = datetime.utcnow().isoformat()
        TaskStore.set_meta(task_id, meta)

        PipelineHistoryDB.mark_success(pipeline, file)


    return

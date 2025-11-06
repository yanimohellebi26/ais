from celery import Celery
import os
import redis
from celery.signals import task_failure
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "etl_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.autodiscover_tasks(["worker"])

redis_client = redis.Redis.from_url(REDIS_URL, db=1, decode_responses=True)


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    from worker.store import TaskStore

    meta = TaskStore.get_meta(task_id)
    if meta.get("status") == "running":
        meta["status"] = "error"
        meta["ended_at"] = datetime.utcnow().isoformat()
        TaskStore.set_meta(task_id, meta)
        TaskStore.append_log(task_id, "pipeline", "error", {
            "pipeline": sender.name,
            "message": str(exception)
        })

import worker.task_command
import worker.task_pipeline

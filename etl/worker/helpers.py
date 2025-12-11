from datetime import datetime
from worker.store import TaskStore


def enqueue_task(task_func, args=None, kwargs=None, user=None, command_name=None):
    """
    Enqueue a Celery task and initialize its metadata in Redis immediately.

    :param task_func: Celery task function
    :param args: positional arguments for the task
    :param kwargs: keyword arguments for the task
    :param user: user who triggered the task
    :param command_name: optional name to store in metadata
    :return: Celery AsyncResult
    """
    args = args or []
    kwargs = kwargs or {}

    # Start
    task = task_func.apply_async(args=args, kwargs=kwargs)
    task_id = task.id
    now = datetime.utcnow().isoformat()

    # Task name
    name = command_name or getattr(task_func, "name", str(task_func))

    # Init in redis
    TaskStore.set_meta(task_id, {
        "task_id": task_id,
        "command": name,
        "pipeline": kwargs.get("pipeline") if name == "run-pipeline" else None,
        "file": kwargs.get("file") if name == "run-pipeline" else None,
        "kwargs": kwargs,
        "user": user,
        "status": "queued",
        "created_at": now,
        "started_at": None,
        "ended_at": None,
    })

    # Log "queued"
    if name == "run-pipeline":
        TaskStore.append_log(task_id, "pipeline", "queued", {"pipeline": kwargs.get("pipeline")})
    else:
        TaskStore.append_log(task_id, "command", "queued", {"command": name})

    return task

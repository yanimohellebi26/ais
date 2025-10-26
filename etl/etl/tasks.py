# etl/tasks.py
from datetime import datetime

from api.celery_app import celery_app
from etl.utils import task_store
import click


@celery_app.task(bind=True, name="run_cli_command")
def run_cli_command(self, command_name, kwargs, user=None):
    from etl.cli import cli
    task_id = self.request.id
    now = datetime.utcnow().isoformat()

    # meta task
    task_store.set_task_meta(task_id, {
        "task_id": task_id,
        "command": command_name,
        "kwargs": kwargs,
        "user": user,
        "status": "queued",
        "created_at": now,
        "started_at": None,
        "ended_at": None,
        "result": None,
        "error": None
    })

    try:
        # update status
        meta = task_store.get_task_meta(task_id)
        meta["status"] = "running"
        meta["started_at"] = datetime.utcnow().isoformat()
        task_store.set_task_meta(task_id, meta)

        # exec CLI
        ctx = click.Context(cli)
        command = cli.get_command(ctx, command_name)
        if not command:
            raise ValueError(f"Command '{command_name}' not found")

        normalized_kwargs = normalize_click_kwargs(command, kwargs)
        if hasattr(command, "callback"):
            result = command.callback(**normalized_kwargs, task_id=task_id)
        else:
            result = command(**normalized_kwargs,task_id=task_id)

        if isinstance(result, dict) and result.get("status") == "error":
            meta = task_store.get_task_meta(task_id)
            meta["status"] = "error"
            meta["ended_at"] = datetime.utcnow().isoformat()
            meta["error"] = result.get("error")
            meta["result"] = str(result)
            task_store.set_task_meta(task_id, meta)
            return result
        else:
            meta = task_store.get_task_meta(task_id)
            meta["status"] = "success"
            meta["ended_at"] = datetime.utcnow().isoformat()
            meta["result"] = str(result)
            task_store.set_task_meta(task_id, meta)
            return {"status": "success", "result": result}

    except Exception as e:
        meta = task_store.get_task_meta(task_id)
        meta["status"] = "error"
        meta["ended_at"] = datetime.utcnow().isoformat()
        meta["error"] = str(e)
        task_store.set_task_meta(task_id, meta)
        return {"status": "error", "error": str(e)}


def normalize_click_kwargs(command, kwargs):
    normalized = {}
    for param in command.params:
        val = kwargs.get(param.name)
        if getattr(param, "is_flag", False):
            if isinstance(val, str):
                normalized[param.name] = val.lower() in ("1", "true", "yes")
            else:
                normalized[param.name] = bool(val)
        else:
            normalized[param.name] = val
    return normalized


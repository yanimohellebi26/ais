from datetime import datetime
import click

from worker.celery_app import celery_app


@celery_app.task(bind=True, name="run_cli_command",soft_time_limit=3600, time_limit=3700)
def run_cli_command(self, command_name, kwargs, user=None):
    from cli.cli import cli
    from worker.store import TaskStore
    from cli.commands.TaskPublisher import TaskPublisher

    task_id = self.request.id
    publisher = TaskPublisher(task_id)
    now = datetime.utcnow().isoformat()

    # --- Initialisation de la tâche --- #
    TaskStore.set_meta(task_id, {
        "task_id": task_id,
        "command": command_name,
        "kwargs": kwargs,
        "user": user,
        "status": "queued",
        "created_at": now,
        "started_at": None,
        "ended_at": None,
    })

    TaskStore.append_log(task_id, "command", "queued", {"command": command_name})

    # --- Start ---
    meta = TaskStore.get_meta(task_id)
    meta["status"] = "running"
    meta["started_at"] = datetime.utcnow().isoformat()
    TaskStore.set_meta(task_id, meta)
    TaskStore.append_log(task_id, "command", "running", {"command": command_name})

    try:
        ctx = click.Context(cli)
        command = cli.get_command(ctx, command_name)
        if not command:
            raise ValueError(f"Command '{command_name}' not found")

        normalized_kwargs = normalize_click_kwargs(command, kwargs)

        # Exécution de la commande
        if hasattr(command, "callback"):
            command.callback(**normalized_kwargs, publisher=publisher)
        else:
            command(**normalized_kwargs, publisher=publisher)

        # --- Success ---
        meta = TaskStore.get_meta(task_id)
        meta["status"] = "success"
        meta["ended_at"] = datetime.utcnow().isoformat()
        TaskStore.set_meta(task_id, meta)
        TaskStore.append_log(task_id, "command", "success", {"command": command_name})

    except Exception as e:
        meta = TaskStore.get_meta(task_id)
        meta["status"] = "error"
        meta["ended_at"] = datetime.utcnow().isoformat()
        TaskStore.set_meta(task_id, meta)
        TaskStore.append_log(task_id, "command", "error", {"command": command_name, "error": str(e)})


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

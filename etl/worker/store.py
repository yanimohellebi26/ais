import json
from worker.celery_app import redis_client
from worker.messages import build_message


class TaskStore:
    """Central monitoring of Celery tasks metadata and logs"""

    # -------------------- METADATA -------------------- #
    @staticmethod
    def set_meta(task_id: str, data: dict):
        redis_client.set(f"task:{task_id}", json.dumps(data))

    @staticmethod
    def get_meta(task_id: str):
        val = redis_client.get(f"task:{task_id}")
        return json.loads(val) if val else None

    @staticmethod
    def list_tasks(status=None):
        keys = redis_client.keys("task:*")
        tasks = []
        for k in keys:
            if ":logs" in k:
                continue
            raw = redis_client.get(k)
            if not raw:
                continue
            task = json.loads(raw)
            if status is None or task.get("status") == status:
                tasks.append(task)
        return tasks

    @staticmethod
    def delete_task(task_id: str):
        redis_client.delete(f"task:{task_id}")
        redis_client.delete(f"task:{task_id}:logs")

    # -------------------- LOGS -------------------- #

    @staticmethod
    def append_log(task_id: str, type_: str, status: str, payload=None):
        """Add structured message to REDIS"""
        entry = build_message(type_=type_, status=status, payload=payload)
        redis_client.rpush(f"task:{task_id}:logs", json.dumps(entry))

    @staticmethod
    def get_logs(task_id: str, limit=None):
        """Get logs task"""
        key = f"task:{task_id}:logs"
        if limit:
            entries = redis_client.lrange(key, -limit, -1)
        else:
            entries = redis_client.lrange(key, 0, -1)
        return [json.loads(e) for e in entries]

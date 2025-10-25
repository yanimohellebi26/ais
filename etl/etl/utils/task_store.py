# etl/utils/task_store.py
import json
from api.celery_app import redis_client

def set_task_meta(task_id: str, data: dict):
    redis_client.set(f"task:{task_id}", json.dumps(data))

def get_task_meta(task_id: str):
    val = redis_client.get(f"task:{task_id}")
    if val:
        return json.loads(val)
    return None

def list_tasks(status=None):
    keys = redis_client.keys("task:*")
    tasks = []
    for k in keys:
        task = json.loads(redis_client.get(k))
        if status is None or task.get("status") == status:
            tasks.append(task)
    return tasks

def delete_task(task_id: str):
    redis_client.delete(f"task:{task_id}")

from datetime import datetime

from fastapi import APIRouter, Depends
from etl.utils import task_store
from api.security_api import verify_api_key
from api.celery_app import celery_app

router = APIRouter()

@router.get("/")
def list_all_tasks(auth=Depends(verify_api_key)):
    """List all tasks sorted by creation date"""
    tasks = task_store.list_tasks()
    tasks_sorted = sorted(tasks, key=lambda t: t["created_at"], reverse=True)
    return tasks_sorted

@router.get("/{task_id}")
def get_task(task_id: str, auth=Depends(verify_api_key)):
    """Get task's state"""
    task = task_store.get_task_meta(task_id)
    if not task:
        return {"error": "Task not found"}
    return task

@router.post("/{task_id}/revoke")
def revoke_task(task_id: str, auth=Depends(verify_api_key)):
    """Kill active task"""
    celery_app.control.revoke(task_id, terminate=True)
    task = task_store.get_task_meta(task_id)
    if task:
        task["status"] = "revoked"
        task["ended_at"] = datetime.utcnow().isoformat()
        task_store.set_task_meta(task_id, task)
    return {"status": "revoked", "task_id": task_id}

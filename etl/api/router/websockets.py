from fastapi import WebSocket, APIRouter, Depends, WebSocketDisconnect
from api.security_api import verify_api_key_token
from worker.store import TaskStore
import asyncio

router = APIRouter()

@router.websocket("/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str, auth=Depends(verify_api_key_token)):
    await websocket.accept()
    last_meta = None
    last_log_count = 0
    try:
        while True:
            meta = TaskStore.get_meta(task_id)
            logs = TaskStore.get_logs(task_id)

            # No task
            if not meta:
                await websocket.send_json({"status": "not_found", "task_id": task_id})
                await websocket.close(code=4004)
                break

            # New logs
            if len(logs) > last_log_count:
                new_logs = logs[last_log_count:]
                await websocket.send_json({"type": "logs", "data": new_logs})
                last_log_count = len(logs)

            # Task end close socket
            if meta["status"] in ("success", "error", "revoked"):
                await websocket.send_json({"type": "end", "data": meta["status"]})
                await asyncio.sleep(0.5)
                await websocket.close(code=1000)
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        print(f"Error in WebSocket for task {task_id}: {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass

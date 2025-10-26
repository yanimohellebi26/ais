from fastapi import WebSocket, APIRouter, Depends, WebSocketDisconnect
from api.security_api import verify_api_key_token
from etl.utils import task_store
import asyncio

router = APIRouter()

@router.websocket("/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str, auth=Depends(verify_api_key_token)):
    await websocket.accept()
    last_status = None
    try:
        while True:
            task_meta = task_store.get_task_meta(task_id)

            # No task
            if not task_meta:
                await websocket.send_json({"status": "not_found", "task_id": task_id})
                await websocket.close(code=4004)
                break

            # state change
            if task_meta != last_status:
                await websocket.send_json(task_meta)
                last_status = task_meta

            # task done
            if task_meta["status"] in ("success", "error"):
                await websocket.send_json({"status": "closed", "reason": task_meta["status"]})
                await asyncio.sleep(0.5)  # delay
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

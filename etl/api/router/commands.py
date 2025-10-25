from fastapi import APIRouter, Depends, HTTPException
from api.security_api import verify_api_key
from etl.tasks import run_cli_command

router = APIRouter()

@router.post("/{name}")
async def run_command(name: str, payload: dict, auth=Depends(verify_api_key)):
    task = run_cli_command.delay(name, payload, auth['user'])
    return {"task_id": task.id, "status": "queued"}

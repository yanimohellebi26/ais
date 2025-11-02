from fastapi import APIRouter, Depends, HTTPException
from api.security_api import verify_api_key
from cli.cli import cli
from worker.task_command import run_cli_command

router = APIRouter()

@router.post("/{name}")
async def run_command(name: str, payload: dict, auth=Depends(verify_api_key)):
    if name == "run-pipeline":
        return {"error": "use the appropriate endpoint /pipeline for this"}
    task = run_cli_command.delay(name, payload, auth['user'])
    return {"task_id": task.id, "status": "queued"}

@router.get("/")
async def list_commands(auth=Depends(verify_api_key)):
    """List all available CLI commands"""
    commands_info = {}

    for name, command in cli.commands.items():
        # ignored pipeline runner
        if name == "run-pipeline":
            continue

        cmd_info = {
            "help": command.help or "",
            "params": []
        }

        # Options / Args
        for param in command.params:
            param_type = getattr(param.type, "name", str(param.type))
            default_value = (
                str(param.default)
                if not isinstance(param.default, (str, int, float, bool, type(None)))
                else param.default
            )

            param_info = {
                "name": param.name,
                "opts": list(param.opts) if getattr(param, "opts", None) else [],
                "required": bool(param.required),
                "type": param_type,
                "default": default_value,
                "help": getattr(param, "help", None),
                "nargs": getattr(param, "nargs", 1),
                "is_flag": getattr(param, "is_flag", False),
            }

            cmd_info["params"].append(param_info)

        commands_info[name] = cmd_info

    return {"commands": commands_info}

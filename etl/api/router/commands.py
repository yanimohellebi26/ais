from fastapi import APIRouter, Depends, HTTPException
from api.security_api import verify_api_key
from etl.cli import cli
from etl.tasks import run_cli_command

router = APIRouter()

@router.post("/{name}")
async def run_command(name: str, payload: dict, auth=Depends(verify_api_key)):
    task = run_cli_command.delay(name, payload, auth['user'])
    return {"task_id": task.id, "status": "queued"}

@router.get("/")
async def list_commands(auth=Depends(verify_api_key)):
    """List all available CLI commands"""
    commands_info = {}

    for name, command in cli.commands.items():
        # ignorer la commande spéciale
        if name == "run-pipeline":
            continue

        cmd_info = {
            "help": command.help or "",
            "params": []
        }

        # Parcourir les options/arguments
        for param in command.params:
            # sécuriser les champs JSON-compatibles
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
            }

            cmd_info["params"].append(param_info)

        commands_info[name] = cmd_info

    return {"commands": commands_info}
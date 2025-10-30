import inspect

import click
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from api.security_api import verify_api_key
from etl.loader import load_pipelines
from worker.task_command import run_cli_command


router = APIRouter()


class PipelineRequest(BaseModel):
    """
    Request to execute pipeline
    - file : path to source file CSV.
    - fail_fast : Stop pipeline at first error.
    - continue_on_error : Ignore errors and continue.
    - use_timer : Active timer.
    - extra_kwargs : Pass dynamics kwargs.
    """
    file: Optional[str] = None
    fail_fast: bool = False
    continue_on_error: bool = False
    use_timer: bool = True
    extra_kwargs: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Dynamics kwargs to override pipelines parameters."
    )

@router.post("/{pipeline_name}")
async def run_pipeline(pipeline_name: str, payload: PipelineRequest, auth=Depends(verify_api_key)):
    kwargs = {
        "pipeline": pipeline_name,
        "file": payload.file,
        "fail_fast": payload.fail_fast,
        "continue_on_error": payload.continue_on_error,
        "use_timer": payload.use_timer,
        "extra_kwargs": payload.extra_kwargs or {},
    }
    task = run_cli_command.delay("run-pipeline", kwargs, auth['user'])
    return {"pipeline": pipeline_name, "task_id": task.id, "status": "queued"}



@router.get("/")
async def list_pipelines(auth=Depends(verify_api_key)):
    """
    List all pipelines defined int YAML
    with desc and attributes of used functions
    """
    pipelines = load_pipelines()
    result = []

    for pipeline_name, steps in pipelines.items():
        step_infos = []

        for func, kwargs in steps:
            sig = inspect.signature(func)
            params = []
            for name, param in sig.parameters.items():
                params.append({
                    "name": name,
                    "type": str(param.annotation) if param.annotation != inspect._empty else "Any",
                    "default": None if param.default == inspect._empty else param.default,
                })

            step_infos.append({
                "function_name": func.__name__,
                "description": inspect.getdoc(func) or "No description provided.",
                "parameters": params,
                "yaml_kwargs": kwargs,
            })

        result.append({
            "pipeline_name": pipeline_name,
            "steps": step_infos,
        })

    return {
        "count": len(result),
        "pipelines": result,
    }


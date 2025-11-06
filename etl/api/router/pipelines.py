import inspect

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from api.security_api import verify_api_key
from etl.loader import load_pipelines
from worker.helpers import enqueue_task
from worker.task_pipeline import run_task_pipeline


router = APIRouter()


class PipelineRequest(BaseModel):
    """
    Request to execute pipeline
    - file : path to source file CSV.
    - continue_on_error : Ignore errors and continue.
    - use_timer : Active timer.
    - extra_kwargs : Pass dynamics kwargs.
    """
    file: Optional[str] = None
    files: Optional[list[str]] = None
    continue_on_error: bool = False
    use_timer: bool = True
    extra_kwargs: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Dynamics kwargs to override pipelines parameters."
    )


@router.post("/{pipeline_name}")
async def run_pipeline(pipeline_name: str, payload: PipelineRequest, auth=Depends(verify_api_key)):
    if payload.files is not None :
        tasks = []
        for file in payload.files:
            task = enqueue_task(
                run_task_pipeline,
                kwargs={
                    "pipeline": pipeline_name,
                    "file": file,
                    "extra_kwargs": payload.extra_kwargs or {},
                    "user": auth["user"],
                    "continue_on_error": payload.continue_on_error,
                    "use_timer": payload.use_timer,
                },
                command_name="run-pipeline"
            )
            tasks.append(task)
        return {"pipeline": pipeline_name, "count": len(tasks), "status": "queued"}
    else:
        task = enqueue_task(
            run_task_pipeline,
            kwargs={
                "pipeline": pipeline_name,
                "file": payload.file,
                "extra_kwargs": payload.extra_kwargs or {},
                "user": auth["user"],
                "continue_on_error": payload.continue_on_error,
                "use_timer": payload.use_timer,
            },
            command_name="run-pipeline"
        )
        return {"pipeline": pipeline_name, "task_id": task.id, "status": "queued"}

@router.get("/")
async def list_pipelines(auth=Depends(verify_api_key)):
    """
    List all pipelines defined in YAML
    with desc and attributes of used functions
    """
    pipelines = load_pipelines()
    result = []

    for pipeline_name, pipeline_def in pipelines.items():
        desc = pipeline_def.get("desc", "")
        steps_list = pipeline_def.get("steps", [])

        step_infos = []

        for func, kwargs in steps_list:
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
            "description": desc,
            "steps": step_infos,
        })

    return {
        "count": len(result),
        "pipelines": result,
    }



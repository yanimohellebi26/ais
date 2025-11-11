import inspect
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy import text

from api.security_api import verify_api_key
from etl.loader import load_pipelines
from worker.task_pipeline import run_task_pipeline
from utils.db import get_session

router = APIRouter()


class PipelineRequest(BaseModel):
    file: Optional[str] = None
    continue_on_error: bool = False
    use_timer: bool = True
    extra_kwargs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dynamic kwargs to override pipeline parameters."
    )


@router.post("/{pipeline_name}")
async def run_pipeline(pipeline_name: str, payload: PipelineRequest, auth=Depends(verify_api_key)):

    if not payload.file:
        raise HTTPException(status_code=400, detail="Le champ 'file' est obligatoire.")

    with get_session() as session:
        existing = session.execute(
            text("""
                SELECT 1 FROM pipeline_file_registry
                WHERE pipeline_name = :p AND filename = :f AND status = 'running'
            """),
            {"p": pipeline_name, "f": payload.file}
        ).scalar()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Une exécution est déjà en cours pour ce fichier et cette pipeline."
            )

        task = run_task_pipeline.delay(
            pipeline_name,
            payload.file,
            payload.extra_kwargs or {},
            payload.continue_on_error,
            payload.use_timer,
            auth["user"]
        )

        return {"pipeline": pipeline_name, "task_id": task.id, "status": "queued"}


@router.get("/")
async def list_pipelines(auth=Depends(verify_api_key)):
    pipelines = load_pipelines()
    result = []

    for name, pipeline_def in pipelines.items():
        desc = pipeline_def.get("desc", "")
        steps_list = pipeline_def.get("steps", [])
        step_infos = []

        for step in steps_list:
            func = step.get("func")
            kwargs = step.get("kwargs", {})

            if not callable(func):
                continue

            sig = inspect.signature(func)
            params = []
            for pname, param in sig.parameters.items():
                params.append({
                    "name": pname,
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
            "pipeline_name": name,
            "description": desc,
            "steps": step_infos,
        })

    return {"count": len(result), "pipelines": result}

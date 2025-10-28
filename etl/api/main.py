from fastapi import FastAPI

from api.router import commands, pipelines, tasks, logs, api_keys, healtcheck

app = FastAPI(title="ETL Orchestrator API")

app.include_router(healtcheck.router,tags=["Healthcheck"])
app.include_router(commands.router, prefix="/commands", tags=["Commands"])
app.include_router(pipelines.router, prefix="/pipelines", tags=["Pipelines"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(api_keys.router, prefix="/apiKeys", tags=["API Keys"])


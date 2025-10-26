from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket

from api.router import commands, pipelines, tasks, logs, api_keys, healtcheck, websockets

app = FastAPI(title="ETL Orchestrator API")

app.add_middleware(  # type: ignore
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def ping():
    return {"message": "pong"}

app.include_router(healtcheck.router,tags=["Healthcheck"])
app.include_router(commands.router, prefix="/commands", tags=["Commands"])
app.include_router(pipelines.router, prefix="/pipelines", tags=["Pipelines"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(api_keys.router, prefix="/apiKeys", tags=["API Keys"])
app.include_router(websockets.router, prefix="/ws", tags=["Websockets"])
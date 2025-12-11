from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.router import commands, pipelines, tasks, logs, api_keys, healtcheck, websockets, files

app = FastAPI(title="ETL Orchestrator API")

app.add_middleware(  # type: ignore
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    message = errors[0].get("msg", "Invalid request")

    return JSONResponse(
        status_code=422,
        content={"detail": message},
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
app.include_router(files.router, prefix="/files", tags=["Files"])
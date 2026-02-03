from contextlib import asynccontextmanager

import logfire
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app_config import app_config
from src.memory.conversation_handler import ConversationHandler
from src.routers import unified_agent_routes
from src import state

logfire_kwargs = {"environment": "local"}
if app_config.LOGFIRE_TOKEN:
    logfire_kwargs["token"] = app_config.LOGFIRE_TOKEN

logfire.configure(**logfire_kwargs)
logfire.instrument_pydantic()
logfire.instrument_pydantic_ai()


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.conversation_handler = ConversationHandler()
    state.conversation_handler.connect_to_database()
    yield
    if state.conversation_handler:
        state.conversation_handler.close()


app = FastAPI(
    title="AWS-FCJ-Project",
    description="API for AWS-FCJ-Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
logfire.instrument_fastapi(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(unified_agent_routes.router)


@app.get("/")
def root():
    return {"message": "Welcome to the AWS-FCJ-Backend API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

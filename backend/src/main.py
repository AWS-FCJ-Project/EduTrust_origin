from contextlib import asynccontextmanager

import logfire
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from src import state
from src.app_config import app_config
from src.extensions import limiter
from src.memory.conversation_handler import ConversationHandler
from src.routers import unified_agent_routes
from src.routers.auth import register, login, password

logfire.configure(
    environment=app_config.ENVIRONMENT,
    token=app_config.LOGFIRE_TOKEN,
    send_to_logfire=True,
)
logfire.instrument_pydantic(record="failure")
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
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logfire.instrument_fastapi(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=app_config.SECRET_KEY,
    https_only=app_config.ENVIRONMENT == "production",
)

app.include_router(unified_agent_routes.router)
app.include_router(register.router, tags=["Auth"])
app.include_router(login.router, tags=["Auth"])
app.include_router(password.router, tags=["Auth"])


@app.get("/")
def root():
    return {"message": "Welcome to the AWS-FCJ-Backend API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

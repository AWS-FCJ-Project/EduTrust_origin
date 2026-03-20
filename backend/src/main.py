from contextlib import asynccontextmanager

import logfire
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src import state
from src.app_config import app_config
from src.extensions import limiter
from src.memory.conversation_handler import ConversationHandler
from src.routers import document_search_routes, translate_routes, unified_agent_routes
from src.routers.auth import login, password, register

logfire.configure(
    environment="local",
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
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate Limiter Configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logfire.instrument_fastapi(app)
# Authorization middleware requires SessionMiddleware
import starlette.middleware.sessions
app.add_middleware(starlette.middleware.sessions.SessionMiddleware, secret_key=app_config.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(unified_agent_routes.router, tags=["Unified Agent"])
app.include_router(translate_routes.router, tags=["Translate"])
app.include_router(document_search_routes.router, tags=["Document Search"])
app.include_router(register.router, tags=["Register"])
app.include_router(login.router, tags=["Login"])
app.include_router(password.router, tags=["Password"])


@app.get("/")
def root():
    return {"message": "Welcome to the AWS-FCJ-Backend API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

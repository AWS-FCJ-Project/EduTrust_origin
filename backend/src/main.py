from contextlib import asynccontextmanager

import logfire
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.app_config import app_config
from src.conversation.conversation_cache import ConversationCache
from src.conversation.conversation_handler import ConversationHandler
from src.database.dynamodb_client import DynamoDBClient
from src.database.redis_client import RedisClient
from src.database.repositories.conversation_repository import ConversationRepository
from src.extensions import limiter
from src.routers import (
    class_routes,
    conversation_routes,
    exam_routes,
    translate_routes,
    unified_agent_routes,
)
from src.routers.auth import login, password, register

try:
    from src.routers import camera_routes
except ModuleNotFoundError as error:
    if error.name not in {"cv2", "numpy", "torch", "ultralytics"}:
        raise
    camera_routes = None

logfire.configure(
    environment="local",
    token=app_config.LOGFIRE_TOKEN,
    send_to_logfire=True,
)
logfire.instrument_pydantic(record="failure")
logfire.instrument_pydantic_ai()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = RedisClient(
        host=app_config.REDIS_CLIENT_HOST,
        password=app_config.REDIS_CLIENT_PASSWORD,
        port=app_config.REDIS_PORT,
        db=app_config.REDIS_DB,
        tls=app_config.REDIS_TLS,
        key_prefix=app_config.REDIS_KEY_PREFIX,
        chat_ttl=app_config.REDIS_CHAT_TTL,
    )
    redis_client.connect_to_database()

    from src.database import PersistenceFacade

    dynamo_client = DynamoDBClient()
    app.state.persistence = PersistenceFacade(dynamo_client)

    from src.detection.violation_logger import set_violation_logger_persistence

    set_violation_logger_persistence(app.state.persistence)

    conversation_cache = ConversationCache(redis_client=redis_client)

    conversation_repo = ConversationRepository(dynamo_client)
    app.state.conversation_handler = ConversationHandler(
        conversation_repo=conversation_repo,
        conversation_cache=conversation_cache,
    )
    yield
    if app.state.conversation_handler:
        app.state.conversation_handler.close()
    redis_client.close()


app = FastAPI(
    title="AWS-FCJ-Project",
    description="API for AWS-FCJ-Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logfire.instrument_fastapi(app)

# Langfuse tracing (optional)
langfuse_client = None
try:
    langfuse_sensitive = getattr(langfuse, "langfuse_sensitive", None)
    if callable(langfuse_sensitive):
        langfuse_client = langfuse_sensitive()  # Uses env vars LANGFUSE_*
        langfuse_client.configure()
except Exception:
    langfuse_client = None


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(unified_agent_routes.router, tags=["Unified Agent"])
app.include_router(conversation_routes.router, tags=["Conversations"])
app.include_router(translate_routes.router, tags=["Translate"])
app.include_router(register.router, tags=["Register"])
app.include_router(login.router, tags=["Login"])
app.include_router(password.router, tags=["Password"])
app.include_router(exam_routes.router)
app.include_router(class_routes.router)
if camera_routes is not None:
    app.include_router(camera_routes.router, tags=["Camera"])


@app.get("/")
def root():
    return {"message": "Welcome to the AWS-FCJ-Backend API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

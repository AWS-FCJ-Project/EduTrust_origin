from contextlib import asynccontextmanager

import logfire
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src import state
from src.app_config import app_config
from src.extensions import limiter
from src.memory.conversation_cache import ConversationCache
from src.memory.conversation_handler import ConversationHandler
from src.memory.redis_client import RedisClient
from src.routers import (
    camera_routes,
    class_routes,
    exam_routes,
    translate_routes,
    unified_agent_routes,
)
from src.routers.auth import login, password, register
from starlette.middleware.sessions import SessionMiddleware

logfire.configure(
    environment="local",
    token=app_config.LOGFIRE_TOKEN,
    send_to_logfire=True,
)
logfire.instrument_pydantic(record="failure")
logfire.instrument_pydantic_ai()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = RedisClient()
    redis_client.connect_to_database()
    conversation_cache = ConversationCache(redis_client=redis_client)

    state.conversation_handler = ConversationHandler(
        conversation_cache=conversation_cache
    )
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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    from datetime import datetime

    path = request.url.path
    method = request.method
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [ACCESS] {method} {path}")

    response = await call_next(request)
    return response


@app.get("/camera/test")
def test_camera_path():
    return {"message": "Cổng /camera/test hoạt động!"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.post("/log") discarded - consolidated to /camera/log

app.include_router(unified_agent_routes.router, tags=["Unified Agent"])
app.include_router(camera_routes.router, tags=["Camera"])
app.include_router(translate_routes.router, tags=["Translate"])
app.include_router(register.router, tags=["Register"])
app.include_router(login.router, tags=["Login"])
app.include_router(password.router, tags=["Password"])
app.include_router(class_routes.router)
app.include_router(exam_routes.router)


import os

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Mount storage directory
storage_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "storage")
)
if not os.path.exists(storage_dir):
    os.makedirs(storage_dir)
app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")


@app.get("/")
def root():
    return {"message": "Welcome to the AWS-FCJ-Backend API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Serve frontend build if exists
frontend_dist = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)

# Disable static frontend serving to avoid interception of API routes
"""
if os.path.exists(frontend_dist):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(frontend_dist, "assets")),
        name="assets",
    )

    @app.get(
        "/{full_path:path}",
        responses={
            403: {"description": "Forbidden"},
            404: {"description": "Not Found"},
        },
    )
    async def serve_frontend(full_path: str):
        # Don't intercept API routes...
        # Don't intercept API routes...
        api_prefixes = ["api", "docs", "redoc", "camera", "classes", "exams", "users"]
        if any(full_path.startswith(p) for p in api_prefixes):
            raise HTTPException(status_code=404)

        # Sanitize path to prevent traversal
        safe_path = os.path.abspath(os.path.join(frontend_dist, full_path))
        if not safe_path.startswith(frontend_dist):
            raise HTTPException(status_code=403, detail="Forbidden")

        if os.path.isfile(safe_path):
            return FileResponse(safe_path)

        # SPA fallback
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Resource not found")
"""


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

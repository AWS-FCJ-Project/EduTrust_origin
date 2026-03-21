from contextlib import asynccontextmanager

import logfire
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src import state
from src.app_config import app_config
from src.extensions import limiter
from src.memory.conversation_handler import ConversationHandler
from src.routers import camera_routes, translate_routes, unified_agent_routes
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
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[ACCESS] {request.method} {request.url.path}")
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(unified_agent_routes.router, tags=["Unified Agent"])
app.include_router(camera_routes.router, tags=["Camera"])
app.include_router(translate_routes.router, tags=["Translate"])
app.include_router(register.router, tags=["Register"])
app.include_router(login.router, tags=["Login"])
app.include_router(password.router, tags=["Password"])

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve frontend build if exists
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't intercept API routes (even though they are mounted above, this is a fallback catch-all)
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("camera/"):
            pass
            
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # SPA fallback
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend build not found at " + frontend_dist}
else:
    @app.get("/")
    def root():
        return {"message": "Welcome to the AWS-FCJ-Backend API. (Frontend build not found)"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

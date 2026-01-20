import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import tutor_agent_routes

app = FastAPI(
    title="AWS-FCJ-Project",
    description="API for AWS-FCJ-Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tutor_agent_routes.router)


@app.get("/")
def root():
    return {"message": "Welcome to the AWS-FCJ-Backend API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# EduTrust - AI Educational Assistant

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)
![Pydantic AI](https://img.shields.io/badge/Pydantic%20AI-E92063?style=flat&logo=pydantic&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=mongodb&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)

> **EduTrust** is a tool-augmented AI assistant designed to provide personalized educational support. Operating as a ReAct-style reasoning agent, it intelligently routes queries to specialist sub-agents (Math, Physics, Literature, etc.) to deliver accurate, step-by-step guidance.

### Key Features
-   **Smart Routing**: Distinguishes between simple queries and complex problems requiring multi-step reasoning.
-   **Specialist Agents**: Dedicated experts for Math, Science, Humanities, and General Knowledge.
-   **Real-time Search**: Integrated web search for current events and fact-checking.

## Project Structure

```
aws-fcj-project/
├── Dockerfile                      # Container build definition
├── backend/                        # FastAPI application
│   ├── config/                     # Agent + LLM YAML configs
│   │   ├── agents.yaml
│   │   └── llms.yaml
│   ├── src/
│   │   ├── crew/                   # Orchestrator + tool wiring
│   │   ├── memory/                 # MongoDB conversation storage
│   │   ├── routers/                # API routes
│   │   ├── schemas/                # Endpoint schemas
│   │   ├── search_services/        # Web search services
│   │   ├── app_config.py           # Env + settings
│   │   ├── logger.py               # Logging helpers
│   │   ├── state.py                # Shared app state
│   │   └── main.py                 # FastAPI entry point
│   ├── test_tools.py               # Local tool smoke tests
│   └── pyproject.toml              # Backend deps
└── frontend/                       # React app (Vite)
    ├── src/
    │   ├── App.tsx
    │   ├── main.tsx
    │   └── styles.css
    ├── index.html
    └── package.json
```

## Prerequisites

Before running the project, ensure you have the following installed:

1.  **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
2.  **Node.js & npm**: [Download Node.js](https://nodejs.org/)
3.  **uv** (An extremely fast Python package installer and resolver):
    ```bash
    pip install uv
    ```

## Backend Setup

The backend is located in the `backend/` directory.

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Install Dependencies:**
    Use `uv` to sync dependencies from `pyproject.toml`.
    ```bash
    uv sync
    ```

3.  **Run the Server:**
    Start the development server with hot-reload enabled.
    ```bash
    uv run uvicorn src.main:app --reload
    ```
    The backend API will be available at `http://localhost:8000`.

## Frontend Setup

The frontend is located in the `frontend/` directory.

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Run Development Server:**
    ```bash
    npm run dev
    ```
4.  **Build for Production:**
    To build the app for deployment:
    ```bash
    npm run build
    ```

## Development Workflow

-   **Backend**: The `uv run` command automatically handles the virtual environment for you.
-   **Frontend**: Vite provides a fast development server with Hot Module Replacement (HMR).

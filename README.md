# EduTrust - AI Educational Assistant

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)
![Pydantic AI](https://img.shields.io/badge/Pydantic%20AI-E92063?style=flat&logo=pydantic&logoColor=white)
![DynamoDB](https://img.shields.io/badge/AWS%20DynamoDB-4053D6?style=flat&logo=amazon-dynamodb&logoColor=white)
![ElastiCache](https://img.shields.io/badge/AWS%20ElastiCache-C925D1?style=flat&logo=amazonaws&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)

> **EduTrust** is an AI-powered educational assistant platform built for schools. It combines a smart routing AI agent (Pydantic AI + LiteLLM) with a full exam management system including proctoring, real-time monitoring, and multi-role authentication.

![Architecture](docs/edutrust-architect.png)

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [System State Machine](#system-state-machine)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Deployment](#deployment)

---

## Overview

EduTrust consists of two parts:

| Component | Description |
|-----------|-------------|
| **AI Agent** | ReAct-style reasoning agent that routes queries to specialist sub-agents (Math, Science, Literature, Web Search) via Pydantic AI |
| **Exam System** | Full exam lifecycle management with secret keys, time-windowed access, auto-scoring, and proctoring via violation logging |

---

## Tech Stack

### Backend

| Category | Technology |
|----------|------------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) 0.128+ |
| AI Agent | [Pydantic AI](https://ai.pydantic.dev/) 1.51|
| Database | AWS [DynamoDB](https://aws.amazon.com/dynamodb/) (boto3) |
| Cache | Redis (ElastiCache) |
| Auth | AWS [Cognito](https://aws.amazon.com/cognito/) (JWT, 3 user groups) |
| Rate Limiting | [SlowAPI](https://github.com/laurentS/slowapi) |
| Observability | [Logfire](https://logfire.pydantic.dev/) (FastAPI instrumentation) + Langfuse (optional) |
| Python Pkg Manager | [UV Astral](https://docs.astral.sh/uv/) |

### Frontend

| Category | Technology |
|----------|------------|
| Framework | [Next.js](https://nextjs.org/) 15 (App Router) |
| UI | [React](https://react.dev/) 19 + [Tailwind CSS](https://tailwindcss.com/) v4 |
| Math Rendering | [KaTeX](https://katex.org/) + [react-markdown](https://remarkjs.github.io/react-markdown/) |
| AI UI | [@openai/apps-sdk-ui](https://openai.com/) |

### Infrastructure

| Category | Technology |
|----------|------------|
| IaC | [Terraform](https://www.terraform.io/) 1.14+ (AWS provider 6.34) |
| CI/CD | [GitHub Actions](.github/workflows/ci.yml) |
| Container | Docker (multi-stage, Ubuntu 24.04 base) |
| Compute | AWS EC2 + Auto Scaling Group + Launch Template |
| Load Balancer | AWS Application Load Balancer (ALB) |
| Cache | AWS [ElastiCache](https://aws.amazon.com/elasticache/) Redis (cluster mode) |
| Frontend Protection | WAFv2 for an existing CloudFront distribution (optional) |

---

## System State Machine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EDUTRUST SYSTEM FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

   ┌──────────┐    login     ┌──────────────┐   create exam   ┌──────────┐
   │ anonymous │────────────▶│  authenticated │───────────────▶│ teacher  │
   └──────────┘              └──────────────┘                │  admin   │
        │                           │                        └────┬─────┘
        │                           │                             │
        │                     refresh token                        │ add students
        │                           │                             │
        │                           ▼                             ▼
        │                    ┌──────────────┐               ┌──────────────┐
        │                    │   expired   │               │ exam ready   │
        │                    │ (re-login)  │               │ (time window)│
        │                    └──────────────┘               └──────┬──────┘
        │                                                      │
        │  ┌───────────────────────────────────────────────────┘
        │  │
        ▼  ▼
  ┌──────────────────────────────────────────────────────────┐
  │                    EXAM LIFECYCLE                         │
  └──────────────────────────────────────────────────────────┘

  ┌──────────────┐  verify key   ┌─────────────┐   submit   ┌────────────┐
  │  not_started │─────────────▶│   active    │───────────▶│  submitted │
  └──────────────┘              │ (can take)  │ (completed)└────────────┘
       │                         │             │
       │ (time before start)     │ (expired)   │ (failed / disqualified)
       └─────────────────────────┼─────────────┘
                                  ▼
                               expired

  ┌──────────────────────────────────────────────────────────┐
  │               PROCTORING (parallel to exam)               │
  └──────────────────────────────────────────────────────────┘

  ┌────────────┐   violation    ┌──────────┐  severity   ┌───────────────┐
  │ monitoring │──────────────▶│ warning  │───────────▶ │ disqualified  │
  └────────────┘                └──────────┘  (high)    └───────────────┘

  ┌──────────────────────────────────────────────────────────┐
  │               AI AGENT (parallel to exam)                 │
  └──────────────────────────────────────────────────────────┘

  ┌──────┐   ask   ┌──────────┐  route   ┌───────────┐ stream ┌─────────┐
  │ idle │────────▶│ routing  │─────────▶│ delegate  │───────▶│ complete│
  └──────┘         └──────────┘          └───────────┘        └─────────┘
```

### System Modules

| Module | Description |
|--------|-------------|
| Auth | Cognito authentication, OTP, session |
| Agent | Pydantic AI orchestrator + sub-agents |
| Conversation | Redis cache + DynamoDB persistence |
| Exam | Exam CRUD + submission flow |
| Detection | Camera proctoring + violation logging |
| Translate | LLM-powered document translation |
| Search | Tavily + unified web search |
| Database | DynamoDB + Redis |

### User Roles & Permissions

| Role | Permissions |
|------|-------------|
| `admin` | Full access — user management, class management, all exams |
| `teacher` | Create/manage exams for assigned classes, view results |
| `student` | Take exams (with secret key + time window), view own results |

---
### ElastiCache Redis

| Setting | Value |
|---------|-------|
| Engine | Redis 7.x (cluster mode enabled) |
| Port | 6379 |
| Replication | Multi-AZ (1 primary + 2 replicas) |
| Use Case | Conversation message cache, session cache |
| Security | VPC endpoint / Security Group egress control |

---

## Getting Started

### Prerequisites
- Python 3.11+ · Node.js 20+ · [UV](https://docs.astral.sh/uv/)

### Backend
```bash
cd backend
uv sync
cp .env.example .env   # configure your values
uv run uvicorn src.main:app --reload --port 8000
```
API docs: `http://localhost:8000/docs` (Swagger), `/redoc` (ReDoc).

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend: `http://localhost:3000`.

---

## Project Structure

```
aws-fcj-project/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                 # CI pipeline
│   │   └── deploy-ec2.yml         # Terraform apply + ECR build + ASG deploy
│   └── terraform/                 # Infrastructure as Code (split across multiple files)
│       ├── providers.tf           # Provider + backend
│       ├── network.tf             # VPC, subnets, routes, NAT
│       ├── data_services.tf       # DynamoDB + ElastiCache
│       ├── app_services.tf        # Cognito, S3, ECR
│       ├── compute.tf             # ALB, launch template, ASG
│       ├── observability.tf       # Flow logs, ALB logs, WAF, alarms
│       ├── security.tf            # KMS, SSM, endpoints, IAM
│       └── outputs.tf             # Terraform outputs
├── Dockerfile                     # Multi-stage container build
├── backend/
│   ├── pyproject.toml            # Python deps (UV)
│   ├── src/
│   │   ├── main.py              # FastAPI entry point + lifespan
│   │   ├── app_config.py        # Pydantic Settings (all env vars)
│   │   ├── extensions.py        # SlowAPI rate limiter
│   │   ├── llm.py               # LiteLLM chat model init
│   │   ├── streaming.py         # SSE utilities
│   │   ├── prompt_template.py  # Agent system prompts
│   │   ├── agent/               # Pydantic AI orchestrator + tools
│   │   │   ├── unified_agent.py
│   │   │   └── tools.py
│   │   ├── auth/                # Cognito auth, dependencies
│   │   │   ├── cognito_auth.py
│   │   │   ├── dependencies.py
│   │   │   ├── email_service.py
│   │   │   └── otp_storage.py
│   │   ├── database/            # DynamoDB + Redis + Repositories
│   │   │   ├── dynamodb_client.py
│   │   │   ├── dynamodb_facade.py
│   │   │   ├── redis_client.py
│   │   │   └── repositories/
│   │   │       ├── user_repository.py
│   │   │       ├── class_repository.py
│   │   │       ├── exam_repository.py
│   │   │       ├── submission_repository.py
│   │   │       ├── violation_repository.py
│   │   │       ├── conversation_repository.py
│   │   │       └── otp_repository.py
│   │   ├── routers/             # API endpoints
│   │   │   ├── auth/ (login, register, password)
│   │   │   ├── exam_routes.py
│   │   │   ├── class_routes.py
│   │   │   ├── unified_agent_routes.py
│   │   │   ├── conversation_routes.py
│   │   │   ├── translate_routes.py
│   │   │   └── camera_routes.py
│   │   ├── schemas/             # Pydantic models
│   │   │   ├── auth_schemas.py
│   │   │   ├── exam_schemas.py
│   │   │   ├── school_schemas.py
│   │   │   └── *.py
│   │   ├── conversation/       # Chat context (Redis cache + DynamoDB)
│   │   │   ├── conversation_handler.py
│   │   │   └── conversation_cache.py
│   │   ├── detection/          # Exam proctoring + violation logging
│   │   │   ├── violation_logger.py
│   │   │   ├── camera_service.py
│   │   │   └── screenshot_utils.py
│   │   ├── translate_service/   # LLM-powered document translation
│   │   │   └── translate.py
│   │   ├── search_services/     # Tavily + unified search
│   │   └── utils/
│   │       └── s3_utils.py
│   └── config/                  # YAML configs for agents and LLMs
│       ├── agents.yaml
│       └── llms.yaml
└── frontend/
    ├── package.json
    ├── src/
    │   ├── app/                # Next.js App Router
    │   ├── components/
    │   ├── lib/
    │   └── styles/
    └── next.config.mjs
```

---

## Deployment

### Infrastructure Provisioning

```bash
cd .github/terraform

# Initialize (downloads providers, connects to S3 remote state)
terraform init

# Plan changes
terraform plan -var-file="terraform.tfvars"

# Apply (creates all AWS resources)
terraform apply -var-file="terraform.tfvars"
```

### CI/CD Pipeline

| Job | Trigger | Description |
|-----|---------|-------------|
| `pre-commit` | PR open | Lint, format, security checks |
| `test` | PR open | `pytest` with coverage (`>80%` target) |
| `terraform-check` | PR open | `terraform fmt` + `validate` + Checkov scan |

> **Note:** Deploy workflow runs on `workflow_run` from CI on `main` or via `workflow_dispatch`. It applies Terraform, builds and pushes the backend image to ECR, updates `/edutrust/backend/env` in SSM with the latest Redis endpoint, and triggers an ASG instance refresh when the launch template changes.

### Container Deployment Flow

```
workflow_run / workflow_dispatch
       │
       ▼
Terraform apply
       │
       ▼
Backend image built and pushed to ECR
       │
       ▼
SSM Parameter Store updated (/edutrust/backend/env)
       │
       ▼
Terraform plan/apply with backend_image_tag
       │
       ▼
ASG Instance Refresh triggered when launch template changes
       │
       ▼
EC2 Launch Template user-data (per instance):
  1. Docker installed (if missing)
  2. ECR login + docker pull
  3. SSM GetParameter → /opt/edutrust/.env
  4. docker run -d --env-file .env
       │
       ▼
ASG health check (ALB /health endpoint)
       │
       ▼
CloudWatch Agent → container logs
```



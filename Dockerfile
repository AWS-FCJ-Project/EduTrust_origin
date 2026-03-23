# ============================================
# Stage 1: BUILD — Ubuntu 24.04 (glibc 2.39)
# kreuzberg wheel requires glibc >= 2.39
# ============================================
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Python 3.11 from deadsnakes PPA (Ubuntu 24.04 only has 3.12 by default)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      software-properties-common \
      gpg-agent && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      python3.11 \
      python3.11-venv \
      python3.11-dev \
      curl \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy source code
COPY backend /app

# Install into virtual env (kreuzberg wheel installs directly — no Rust needed!)
RUN uv venv --python python3.11 /opt/venv && \
    uv pip install --python /opt/venv/bin/python --no-cache .

# ============================================
# Stage 2: RUNTIME — minimal Ubuntu 24.04
# ============================================
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV="/opt/venv"

# Install only Python 3.11 runtime (no dev/build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      software-properties-common \
      gpg-agent && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      python3.11 \
      ca-certificates && \
    apt-get purge -y software-properties-common gpg-agent && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pre-built virtual env from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY backend /app

# Run as non-root user (security best practice)
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app /opt/venv
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

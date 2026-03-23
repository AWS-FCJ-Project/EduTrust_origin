# ============================================
# Stage 1: BUILD
# ============================================
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.cargo/bin:${PATH}"

# Cài Python 3.11 + build tools + Rust (kreuzberg 4.5.3 LUÔN build từ source)
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
      ca-certificates \
      build-essential \
      pkg-config \
      libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Cài Rust (bắt buộc để build kreuzberg)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

# Cài uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy pyproject.toml trước (layer cache tốt hơn)
COPY backend/pyproject.toml backend/uv.lock* /app/

# Tạo venv và cài dependencies (bước nặng, cache lại nếu pyproject không đổi)
RUN uv venv --python python3.11 /opt/venv && \
    uv pip install --python /opt/venv/bin/python --no-cache .

# Copy source sau (thay đổi code không invalidate cache bước install)
COPY backend /app

# ============================================
# Stage 2: RUNTIME
# ============================================
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV="/opt/venv"

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

COPY --from=builder /opt/venv /opt/venv
COPY backend /app

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app /opt/venv
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
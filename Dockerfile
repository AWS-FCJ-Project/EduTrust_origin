# ==========================================
# GIAI ĐOẠN 1: BUILDER
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.11-noble AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

ENV UV_PYTHON_PREFERENCE=only-system

COPY backend/pyproject.toml backend/uv.lock* /app/

# Dùng --only-binary :all: để force dùng prebuilt wheel, tránh compile Rust từ source
RUN uv venv /opt/venv && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache --only-binary :all: .


# ==========================================
# GIAI ĐOẠN 2: RUNTIME
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.11-noble-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl pandoc tesseract-ocr libmagic1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

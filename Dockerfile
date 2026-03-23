# ==========================================
# GIAI ĐOẠN 1: BUILDER (Sử dụng Ubuntu 24.04 + Python 3.11 có sẵn)
# ==========================================
# Ảnh này của Astral (hãng làm ra uv) đã cài sẵn Python 3.11 trên Ubuntu 24.04 (glibc 2.39)
FROM ghcr.io/astral-sh/uv:python3.11-noble AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Ưu tiên sử dụng Python hệ thống của image để khớp với glibc 2.39
ENV UV_PYTHON_PREFERENCE=only-system

# Cài Rust toolchain để build các package cần compile (vd: kreuzberg/maturin)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:$PATH"

COPY backend/pyproject.toml backend/uv.lock* /app/

RUN uv venv /opt/venv && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache .


# ==========================================
# GIAI ĐOẠN 2: RUNTIME (Đồng bộ bản Noble Slim)
# ==========================================
# Sử dụng bản slim của cùng hệ điều hành (Ubuntu 24.04) có sẵn Python 3.11
FROM ghcr.io/astral-sh/uv:python3.11-noble-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Cài đặt các thư viện runtime mà kreuzberg yêu cầu
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl pandoc tesseract-ocr libmagic1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Tạo user để pass SonarQube
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser

# Copy virtualenv từ builder sang
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code (root sở hữu để đảm bảo read-only cho appuser)
COPY backend /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
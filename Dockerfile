# ==========================================
# GIAI ĐOẠN 1: BUILDER (Ubuntu 24.04 có glibc 2.39)
# ==========================================
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Cài đặt các công cụ cần thiết để uv hoạt động và build (nếu cần)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl build-essential pkg-config libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Lấy uv bản mới nhất
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

COPY backend/pyproject.toml backend/uv.lock* /app/

# Bước quan quan trọng:
# 1. Ubuntu 24.04 có glibc 2.39 -> UV sẽ tải được bản wheel (.whl) đã build sẵn của kreuzberg
# 2. Không cần phải cài Rust hay chờ compile 10 phút nữa.
RUN uv venv /opt/venv --python 3.11 && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache .


# ==========================================
# GIAI ĐOẠN 2: RUNTIME (Ubuntu 24.04 đồng bộ)
# ==========================================
FROM ubuntu:24.04

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
# ==========================================
# GIAI ĐOẠN 1: BUILDER (Chứa toàn bộ compiler)
# ==========================================
# Sử dụng image Python ĐẦY ĐỦ (chứa sẵn gcc, cc, g++, libssl-dev, python3-dev...)
FROM python:3.11-bookworm AS builder

# Cài đặt Rust (Cargo/Maturin cần Rust để compile kreuzberg)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy công cụ uv siêu tốc từ ảnh chính thức
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock* /app/

# Tạo virtualenv và cài đặt toàn bộ package (Kể cả compile từ source)
RUN uv venv /opt/venv --python 3.11 && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache .


# ==========================================
# GIAI ĐOẠN 2: RUNTIME (Siêu nhẹ, bảo mật)
# ==========================================
# Sử dụng bản slim để chạy app (Nhẹ, không chứa gcc/thư viện thừa)
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Cài đặt CÁC THƯ VIỆN RUNTIME cần thiết cho kreuzberg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    pandoc tesseract-ocr && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy toàn bộ virtualenv ĐÃ ĐƯỢC COMPILE từ giai đoạn 1 sang
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code của ứng dụng
COPY backend /app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
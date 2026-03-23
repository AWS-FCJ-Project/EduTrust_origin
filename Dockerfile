FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Cài gcc/linker TRƯỚC, sau đó Rust
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc g++ \
    build-essential \
    curl pkg-config libssl-dev \
    libmagic1 libmagic-dev \
    pandoc tesseract-ocr && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable && \
    /root/.cargo/bin/rustup target add x86_64-unknown-linux-gnu

ENV PATH="/root/.cargo/bin:${PATH}"
ENV CARGO_HOME="/root/.cargo"
ENV RUSTUP_HOME="/root/.rustup"
# Bắt buộc: báo cho cargo biết dùng gcc nào
ENV CC=gcc
ENV CXX=g++
ENV CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER=gcc

COPY backend/pyproject.toml backend/uv.lock* /app/

RUN uv pip install --system --no-cache .

COPY backend /app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
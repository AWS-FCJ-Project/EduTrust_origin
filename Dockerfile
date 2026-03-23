FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install runtime dependencies for kreuzberg (pandoc & tesseract)
# We use Ubuntu 24.04 because it has a new enough glibc (2.39) to download
# the pre-compiled wheel for kreuzberg, avoiding a 10-minute Rust build from source!
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl pandoc tesseract-ocr && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Get uv binary
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

COPY backend/pyproject.toml backend/uv.lock* /app/

# uv will automatically fetch python 3.11 and install dependencies using pre-built wheels
RUN uv venv /opt/venv --python 3.11 && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache .

ENV PATH="/opt/venv/bin:$PATH"

COPY backend /app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

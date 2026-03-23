# ============================================
# Stage 1: BUILD — full compiler + Rust toolchain
# ============================================
FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS builder

WORKDIR /app

# Install build tools + Rust (needed for kreuzberg - mixed Python/Rust package)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      pkg-config \
      libssl-dev \
      curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

# Copy source code
COPY backend /app

# Install into a virtual env for clean copy to runtime stage
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python --no-cache .

# ============================================
# Stage 2: RUNTIME — slim image, no compiler
# ============================================
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy pre-built virtual env from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY backend /app

ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV="/opt/venv"

# Run as non-root user (security best practice)
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app /opt/venv
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

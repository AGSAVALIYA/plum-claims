# ── Base Stage ──────────────────────────────────────────────
FROM python:3.13-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system deps (OpenCV, Docling, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dependencies Layer (cached unless pyproject/uv.lock change) ─
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --compile-bytecode

# ── Application ────────────────────────────────────────────
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY assignment/ ./assignment/

# Install the project itself as a package
RUN uv sync --no-dev

# Create non-root user and give ownership of /app to appuser
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser \
    && mkdir -p /app/backend/uploads \
    && chown -R appuser:appuser /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_CACHE_DIR=/tmp/.cache/uv

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

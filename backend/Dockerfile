# ===========================================================================
# AegisAPI Backend Dockerfile (FastAPI + Isolation Forest ML Engine)
# Multi-stage production build with non-root security principles and healthcheck
# ===========================================================================

# --- Stage 1: Build & Dependency Wheel Cache ---
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Final Minimal Runtime Image ---
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app \
    MODELS_DIR=/app/models \
    DATABASE_URL=sqlite:////app/aegisapi.db

# Copy installed python dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application backend source code
COPY app /app/app

# Create persistent storage directories
RUN mkdir -p /app/models

EXPOSE 8000

# Container healthcheck querying the active health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


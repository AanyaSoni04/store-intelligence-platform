# ============================================================
# Store Intelligence System — Dockerfile
# Multi-stage build for lean production image
# ============================================================

# ── Stage 1: Dependencies ──────────────────────────────────
FROM python:3.11-slim AS deps

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Application ───────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy source code
COPY src/ src/
COPY configs/ configs/
COPY dashboard/ dashboard/
COPY scripts/ scripts/
COPY pyproject.toml .

# Install the package in editable-ish mode so imports work
ENV PYTHONPATH="/app/src"

# Create data directory for SQLite
RUN mkdir -p /app/data

EXPOSE 8000

# TODO: Add healthcheck
# HEALTHCHECK --interval=30s --timeout=5s \
#   CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "store_intel.main:app", "--host", "0.0.0.0", "--port", "8000"]

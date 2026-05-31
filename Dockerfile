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

# Install system-level graphics and X11 libraries required by OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libx11-xcb1 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*

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

# The default entrypoint is the API server. 
# The pipeline worker overrides this via the `command` directive in docker-compose.yml.
CMD ["uvicorn", "store_intel.main:app", "--host", "0.0.0.0", "--port", "8000"]

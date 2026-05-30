"""
FastAPI application entrypoint.

This is the main module that wires everything together:
    - Initializes the database
    - Configures structured logging
    - Mounts all API routes
    - Serves the dashboard as static files
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from store_intel.config import settings
from store_intel.logging import setup_logging
from store_intel.db.engine import init_db

# Import route modules
from store_intel.api import ingest, metrics, funnel, heatmap, anomalies, health, websocket

logger = logging.getLogger("store_intel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # ── Startup ─────────────────────────────────────────────
    setup_logging()
    logger.info("Starting Store Intelligence System", extra={"version": settings.version})

    # Create database tables
    init_db()
    logger.info("Database initialized", extra={"url": settings.database_url})

    yield

    # ── Shutdown ────────────────────────────────────────────
    logger.info("Shutting down Store Intelligence System")


# ── App instance ────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="End-to-end pipeline converting CCTV footage into real-time retail analytics.",
    lifespan=lifespan,
)

# ── Register routes ─────────────────────────────────────────
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(metrics.router)
app.include_router(funnel.router)
app.include_router(heatmap.router)
app.include_router(anomalies.router)
app.include_router(websocket.router)

# ── Serve dashboard static files ────────────────────────────
dashboard_path = Path(__file__).resolve().parent.parent.parent / "dashboard"
if dashboard_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")


# ── Root redirect ───────────────────────────────────────────
@app.get("/", tags=["System"])
def root():
    """Root endpoint — redirects to API docs."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
        "dashboard": "/dashboard",
    }

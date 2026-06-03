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

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from store_intel.config import settings
from store_intel.logging import setup_logging
from store_intel.db.engine import init_db

# Import route modules
from store_intel.api import ingest, metrics, funnel, heatmap, anomalies, health, websocket, camera, telemetry, staff

import sqlite3
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you might want to replace "*" with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(SQLAlchemyOperationalError)
async def sqlalchemy_operational_error_handler(request: Request, exc: SQLAlchemyOperationalError):
    logger.error("Database OperationalError", exc_info=True)
    return JSONResponse(
        status_code=503,
        content={"detail": "Service Unavailable: Database connection failed."}
    )

@app.exception_handler(sqlite3.OperationalError)
async def sqlite3_operational_error_handler(request: Request, exc: sqlite3.OperationalError):
    logger.error("SQLite OperationalError", exc_info=True)
    return JSONResponse(
        status_code=503,
        content={"detail": "Service Unavailable: Database connection failed."}
    )

# ── Register routes ─────────────────────────────────────────
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(metrics.router)
app.include_router(funnel.router)
app.include_router(heatmap.router)
app.include_router(anomalies.router)
app.include_router(websocket.router)
app.include_router(camera.router)
app.include_router(telemetry.router)
app.include_router(staff.router)

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

"""
GET /health — System health check endpoint.
"""

import time
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from store_intel.config import settings
from store_intel.db.engine import get_db
from store_intel.events.schemas import HealthResponse

logger = logging.getLogger("store_intel")
router = APIRouter(tags=["System"])

# Track startup time for uptime calculation
_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """
    System health check.

    Verifies database connectivity and returns basic system info.
    """
    # Check database connectivity
    db_status = "connected"
    event_count = 0
    try:
        result = db.execute(text("SELECT COUNT(*) FROM events"))
        event_count = result.scalar() or 0
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error("Health check DB failure", extra={"error": str(e)})

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        db=db_status,
        uptime_seconds=round(time.time() - _start_time, 1),
        version=settings.version,
        event_count=event_count,
    )

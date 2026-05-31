"""
GET /stores/{store_id}/metrics — KPI snapshot endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from store_intel.db.engine import get_db
from store_intel.events.schemas import MetricsResponse
from store_intel.analytics.metrics import compute_metrics

router = APIRouter(tags=["Analytics"])


@router.get("/stores/{store_id}/metrics", response_model=MetricsResponse)
def get_metrics(
    store_id: str,
    window: str = Query(default="1h", description="Time window: 5m, 15m, 1h, 1d"),
    db: Session = Depends(get_db),
) -> MetricsResponse:
    """
    Return current KPI snapshot for a store.
    """
    return compute_metrics(db, store_id, window)

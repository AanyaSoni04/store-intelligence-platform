"""
GET /stores/{store_id}/funnel — Visitor funnel endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from store_intel.db.engine import get_db
from store_intel.events.schemas import FunnelResponse
from store_intel.analytics.funnel import compute_funnel

router = APIRouter(tags=["Analytics"])


@router.get("/stores/{store_id}/funnel", response_model=FunnelResponse)
def get_funnel(
    store_id: str,
    window: str = Query(default="1d", description="Time window: 1h, 1d, 7d"),
    db: Session = Depends(get_db),
) -> FunnelResponse:
    """
    Return visitor funnel stages and drop-off rates.
    """
    return compute_funnel(db, store_id, window)

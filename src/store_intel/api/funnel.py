"""
GET /stores/{store_id}/funnel — Visitor funnel endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from store_intel.db.engine import get_db
from store_intel.events.schemas import FunnelResponse

router = APIRouter(tags=["Analytics"])


@router.get("/stores/{store_id}/funnel", response_model=FunnelResponse)
def get_funnel(
    store_id: str,
    window: str = Query(default="1d", description="Time window: 1h, 1d, 7d"),
    db: Session = Depends(get_db),
) -> FunnelResponse:
    """
    Return visitor funnel stages and drop-off rates.

    Funnel stages:
        entered → browsed_zone → joined_queue → completed_billing → exited

    TODO: Implement funnel computation in analytics/funnel.py
    TODO: Compute drop-off rates between consecutive stages
    """
    # TODO: Call analytics.funnel.compute_funnel(db, store_id, window)
    return FunnelResponse(
        store_id=store_id,
        window=window,
        stages=[],
        drop_off_rates={},
    )

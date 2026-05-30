"""
GET /stores/{store_id}/heatmap — Zone visit heatmap endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from store_intel.db.engine import get_db
from store_intel.events.schemas import HeatmapResponse

router = APIRouter(tags=["Analytics"])


@router.get("/stores/{store_id}/heatmap", response_model=HeatmapResponse)
def get_heatmap(
    store_id: str,
    window: str = Query(default="1d", description="Time window: 1h, 1d, 7d"),
    db: Session = Depends(get_db),
) -> HeatmapResponse:
    """
    Return zone-level visit frequency and average dwell time.

    TODO: Implement heatmap computation in analytics/heatmap.py
    TODO: Query ZONE_ENTER/ZONE_EXIT event pairs to compute per-zone metrics
    """
    # TODO: Call analytics.heatmap.compute_heatmap(db, store_id, window)
    return HeatmapResponse(
        store_id=store_id,
        zones=[],
    )

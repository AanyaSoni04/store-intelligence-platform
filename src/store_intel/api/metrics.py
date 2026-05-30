"""
GET /stores/{store_id}/metrics — KPI snapshot endpoint.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from store_intel.db.engine import get_db
from store_intel.events.schemas import MetricsResponse

router = APIRouter(tags=["Analytics"])


@router.get("/stores/{store_id}/metrics", response_model=MetricsResponse)
def get_metrics(
    store_id: str,
    window: str = Query(default="1h", description="Time window: 5m, 15m, 1h, 1d"),
    db: Session = Depends(get_db),
) -> MetricsResponse:
    """
    Return current KPI snapshot for a store.

    Metrics computed:
        - unique_visitors: COUNT(DISTINCT visitor_id) for ENTRY events
        - conversion_rate: completed_billing / unique_visitors
        - avg_dwell_seconds: AVG(total_dwell) from EXIT event metadata
        - queue_depth: current count of visitors in billing zone
        - abandonment_rate: abandoned / (abandoned + completed)

    TODO: Implement metric computation in analytics/metrics.py
    TODO: Parse `window` parameter into from/to datetime range
    """
    # TODO: Call analytics.metrics.compute_metrics(db, store_id, window)
    return MetricsResponse(
        store_id=store_id,
        window=window,
        unique_visitors=0,
        conversion_rate=0.0,
        avg_dwell_seconds=0.0,
        queue_depth=0,
        abandonment_rate=0.0,
        computed_at=datetime.now(timezone.utc),
    )

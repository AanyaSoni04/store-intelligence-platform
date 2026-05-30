"""
GET /stores/{store_id}/anomalies — Anomaly detection endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from store_intel.db.engine import get_db
from store_intel.events.schemas import AnomalyResponse

router = APIRouter(tags=["Analytics"])


@router.get("/stores/{store_id}/anomalies", response_model=AnomalyResponse)
def get_anomalies(
    store_id: str,
    severity: str | None = Query(default=None, description="Filter: low, medium, high"),
    window: str = Query(default="1h", description="Time window: 1h, 1d"),
    db: Session = Depends(get_db),
) -> AnomalyResponse:
    """
    Return detected anomalies for a store.

    Anomaly types:
        - unusual_dwell: visitor dwells > threshold in a zone
        - queue_buildup: queue depth exceeds max
        - empty_store: zero entries for extended period
        - high_abandonment: abandonment rate above threshold

    TODO: Implement anomaly detection in analytics/anomalies.py
    TODO: Filter by severity if provided
    """
    # TODO: Call analytics.anomalies.detect_anomalies(db, store_id, window, severity)
    return AnomalyResponse(anomalies=[])

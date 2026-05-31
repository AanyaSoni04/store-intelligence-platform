"""
KPI metrics computation.

Computes all five core metrics from the events table:
    1. unique_visitors: COUNT(DISTINCT visitor_id) for ENTRY events
    2. conversion_rate: completed_billing / unique_visitors
    3. avg_dwell_seconds: AVG(total_dwell) from EXIT event metadata
    4. queue_depth: active visitors in billing zone (QUEUE_JOIN without matching EXIT)
    5. abandonment_rate: abandoned / (abandoned + completed)

TODO: Implement compute_metrics() with the following approach:
    - Parse window string into (from_time, to_time) datetime range
    - Run SQL queries against the events table with time + staff filters
    - Extract dwell_seconds from metadata_json using json_extract (SQLite)
    - Return MetricsResponse
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from store_intel.events.schemas import MetricsResponse

logger = logging.getLogger("store_intel")


def parse_window(window: str) -> int:
    """Convert window string to seconds."""
    mapping = {"5m": 300, "15m": 900, "1h": 3600, "1d": 86400, "7d": 604800}
    return mapping.get(window, 3600)


def compute_metrics(db: Session, store_id: str, window: str) -> MetricsResponse:
    """Compute KPI snapshot for a store within a time window."""
    window_seconds = parse_window(window)
    from_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)

    # 1. Unique visitors (ENTRY events, exclude staff)
    q1 = text("""
        SELECT COUNT(DISTINCT e.visitor_id) 
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type = 'ENTRY' 
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
    """)
    unique_visitors = db.execute(q1, {"store_id": store_id, "from_time": from_time}).scalar() or 0

    # 2. Conversion rate (PURCHASE_PROXY / unique_visitors)
    q2 = text("""
        SELECT COUNT(DISTINCT e.visitor_id) 
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type = 'PURCHASE_PROXY' 
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
    """)
    purchases = db.execute(q2, {"store_id": store_id, "from_time": from_time}).scalar() or 0
    conversion_rate = (purchases / unique_visitors) if unique_visitors > 0 else 0.0

    # 3. Average dwell seconds (from EXIT events)
    q3 = text("""
        SELECT AVG(COALESCE(json_extract(e.metadata_json, '$.total_dwell_seconds'), json_extract(e.metadata_json, '$.dwell_seconds'))) 
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type = 'EXIT' 
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
    """)
    avg_dwell_seconds = db.execute(q3, {"store_id": store_id, "from_time": from_time}).scalar() or 0.0

    # 4. Abandonment rate (BILLING_QUEUE_ABANDON)
    q4 = text("""
        SELECT COUNT(*) 
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type = 'BILLING_QUEUE_ABANDON' 
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
    """)
    abandonments = db.execute(q4, {"store_id": store_id, "from_time": from_time}).scalar() or 0
    abandonment_rate = (abandonments / (abandonments + purchases)) if (abandonments + purchases) > 0 else 0.0

    # 5. Queue depth (Active visitors in queue = JOINs - (ABANDONs + PURCHASE_PROXY + EXITs))
    q5_join = text("""
        SELECT COUNT(*) FROM events 
        WHERE store_id = :store_id AND event_type = 'BILLING_QUEUE_JOIN' AND timestamp >= :from_time
    """)
    total_joins = db.execute(q5_join, {"store_id": store_id, "from_time": from_time}).scalar() or 0
    
    q5_leave = text("""
        SELECT COUNT(*) FROM events 
        WHERE store_id = :store_id AND event_type IN ('BILLING_QUEUE_ABANDON', 'PURCHASE_PROXY', 'EXIT') AND timestamp >= :from_time
    """)
    total_leaves = db.execute(q5_leave, {"store_id": store_id, "from_time": from_time}).scalar() or 0
    
    queue_depth = max(0, total_joins - total_leaves)

    return MetricsResponse(
        store_id=store_id,
        window=window,
        unique_visitors=unique_visitors,
        conversion_rate=float(conversion_rate),
        avg_dwell_seconds=float(avg_dwell_seconds),
        queue_depth=queue_depth,
        abandonment_rate=float(abandonment_rate),
        computed_at=datetime.now(timezone.utc)
    )

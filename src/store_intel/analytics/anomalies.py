"""
Rule-based anomaly detection.

Four anomaly types at MVP:
    A1 — unusual_dwell:    visitor dwells > T_max_dwell in any zone
    A2 — queue_buildup:    active queue count > Q_max
    A3 — empty_store:      zero ENTRY events for > T_empty during business hours
    A4 — high_abandonment: abandonment rate > A_threshold in window

TODO: Implement detect_anomalies() with the following approach:
    - Run each check as a single SQL query against the events table
    - Return list of Anomaly objects
    - Support severity filtering
    - Consider anomaly cooldown to suppress duplicates
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from store_intel.events.schemas import AnomalyResponse, Anomaly
from store_intel.analytics.metrics import parse_window

logger = logging.getLogger("store_intel")


def detect_anomalies(
    db: Session,
    store_id: str,
    window: str,
    severity: str | None = None,
) -> AnomalyResponse:
    """Run all anomaly checks for a store within a time window."""
    window_seconds = parse_window(window)
    from_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)

    anomalies = []
    
    anomalies.extend(_check_unusual_dwell(db, store_id, from_time))
    anomalies.extend(_check_queue_buildup(db, store_id, from_time))
    anomalies.extend(_check_high_abandonment(db, store_id, from_time))

    if severity:
        anomalies = [a for a in anomalies if a.severity == severity]

    return AnomalyResponse(anomalies=anomalies)


def _check_unusual_dwell(db: Session, store_id: str, from_time: datetime) -> list[Anomaly]:
    """Find ZONE_EXIT events where dwell_seconds > 300."""
    q = text("""
        SELECT e.visitor_id, e.timestamp, 
               json_extract(e.metadata_json, '$.zone_id') as zone_id,
               COALESCE(json_extract(e.metadata_json, '$.total_dwell_seconds'), json_extract(e.metadata_json, '$.dwell_seconds')) as dwell
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type = 'ZONE_EXIT'
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
    """)
    results = db.execute(q, {"store_id": store_id, "from_time": from_time}).fetchall()
    
    anomalies = []
    for row in results:
        dwell = row.dwell
        if dwell and float(dwell) > 300:
            anomalies.append(Anomaly(
                type="unusual_dwell",
                severity="medium",
                description=f"Visitor {row.visitor_id} dwelled unusually long ({float(dwell):.1f}s) in zone {row.zone_id}",
                detected_at=datetime.fromisoformat(row.timestamp) if isinstance(row.timestamp, str) else row.timestamp,
                visitor_id=row.visitor_id,
                zone_id=row.zone_id
            ))
    return anomalies


def _check_queue_buildup(db: Session, store_id: str, from_time: datetime) -> list[Anomaly]:
    """Flag if queue depth > 5."""
    q_join = text("SELECT COUNT(*) FROM events WHERE store_id = :s AND event_type = 'BILLING_QUEUE_JOIN' AND timestamp >= :t")
    q_leave = text("SELECT COUNT(*) FROM events WHERE store_id = :s AND event_type IN ('BILLING_QUEUE_ABANDON', 'PURCHASE_PROXY', 'EXIT') AND timestamp >= :t")
    
    joins = db.execute(q_join, {"s": store_id, "t": from_time}).scalar() or 0
    leaves = db.execute(q_leave, {"s": store_id, "t": from_time}).scalar() or 0
    depth = max(0, joins - leaves)
    
    if depth > 5:
        return [Anomaly(
            type="queue_buildup",
            severity="high",
            description=f"Active queue depth is currently {depth} (threshold: 5).",
            detected_at=datetime.now(timezone.utc)
        )]
    return []


def _check_high_abandonment(db: Session, store_id: str, from_time: datetime) -> list[Anomaly]:
    """Flag if abandonment rate > 0.3 (30%)."""
    q_ab = text("SELECT COUNT(*) FROM events WHERE store_id = :s AND event_type = 'BILLING_QUEUE_ABANDON' AND timestamp >= :t")
    q_pu = text("SELECT COUNT(*) FROM events WHERE store_id = :s AND event_type = 'PURCHASE_PROXY' AND timestamp >= :t")
    
    abandonments = db.execute(q_ab, {"s": store_id, "t": from_time}).scalar() or 0
    purchases = db.execute(q_pu, {"s": store_id, "t": from_time}).scalar() or 0
    total = abandonments + purchases
    
    if total > 0:
        rate = abandonments / total
        if rate > 0.3:
            return [Anomaly(
                type="high_abandonment",
                severity="high",
                description=f"Queue abandonment rate is unusually high at {rate*100:.1f}% ({abandonments}/{total} left queue).",
                detected_at=datetime.now(timezone.utc)
            )]
    return []

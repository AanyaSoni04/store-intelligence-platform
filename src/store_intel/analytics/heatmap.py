"""
Zone-level heatmap computation.

Computes per-zone metrics from ZONE_ENTER and ZONE_EXIT event pairs:
    - visit_count: number of times a zone was entered
    - avg_dwell_seconds: average time spent in the zone

TODO: Implement compute_heatmap() with the following approach:
    - Query ZONE_ENTER events grouped by zone_id (from metadata_json)
    - Query ZONE_EXIT events to get dwell_seconds (from metadata_json)
    - Aggregate per zone
    - Return HeatmapResponse
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from store_intel.events.schemas import HeatmapResponse, ZoneHeat
from store_intel.analytics.metrics import parse_window

logger = logging.getLogger("store_intel")


def compute_heatmap(db: Session, store_id: str, window: str) -> HeatmapResponse:
    """Compute zone heatmap for a store within a time window."""
    window_seconds = parse_window(window)
    from_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)

    q = text("""
        SELECT 
            json_extract(e.metadata_json, '$.zone_id') as zone_id,
            SUM(CASE WHEN e.event_type = 'ZONE_ENTER' THEN 1 ELSE 0 END) as visit_count,
            AVG(CASE WHEN e.event_type = 'ZONE_EXIT' THEN 
                COALESCE(json_extract(e.metadata_json, '$.total_dwell_seconds'), json_extract(e.metadata_json, '$.dwell_seconds')) 
            ELSE NULL END) as avg_dwell
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type IN ('ZONE_ENTER', 'ZONE_EXIT')
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
        GROUP BY zone_id
        HAVING zone_id IS NOT NULL
    """)

    results = db.execute(q, {"store_id": store_id, "from_time": from_time}).fetchall()

    zones = []
    for row in results:
        zone_id = row[0]
        visit_count = row[1] or 0
        avg_dwell = row[2] or 0.0
        
        zones.append(ZoneHeat(
            zone_id=zone_id,
            visit_count=visit_count,
            avg_dwell_seconds=float(avg_dwell)
        ))

    return HeatmapResponse(
        store_id=store_id,
        zones=zones
    )

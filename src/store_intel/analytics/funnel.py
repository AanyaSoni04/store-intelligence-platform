"""
Visitor funnel stage aggregation.

Funnel stages (in order):
    1. entered       — COUNT of ENTRY events
    2. browsed_zone  — COUNT of visitors with at least one ZONE_ENTER
    3. joined_queue  — COUNT of visitors with BILLING_QUEUE_JOIN
    4. completed_billing — COUNT of visitors who dwelled ≥ threshold in billing zone
    5. exited        — COUNT of EXIT events

Drop-off rate between stages:
    drop_off = 1.0 - (next_stage_count / current_stage_count)

TODO: Implement compute_funnel() with the following approach:
    - Query DISTINCT visitor_ids per event type within the time window
    - Count visitors progressing through each stage
    - Compute drop-off rates between consecutive stages
    - Return FunnelResponse
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from store_intel.events.schemas import FunnelResponse, FunnelStage
from store_intel.analytics.metrics import parse_window

logger = logging.getLogger("store_intel")


def compute_funnel(db: Session, store_id: str, window: str) -> FunnelResponse:
    """Compute visitor funnel for a store within a time window."""
    window_seconds = parse_window(window)
    from_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)

    # Helper function to count distinct visitors for a set of event types
    def count_visitors(event_types: list[str]) -> int:
        if not event_types:
            return 0
        placeholders = ','.join([f"'{t}'" for t in event_types])
        q = text(f"""
            SELECT COUNT(DISTINCT e.visitor_id) 
            FROM events e
            JOIN visitors v ON e.visitor_id = v.visitor_id
            WHERE e.store_id = :store_id 
              AND e.event_type IN ({placeholders})
              AND e.timestamp >= :from_time
              AND v.is_staff = 0
        """)
        return db.execute(q, {"store_id": store_id, "from_time": from_time}).scalar() or 0

    c_entered = count_visitors(['ENTRY'])
    c_browsed = count_visitors(['ZONE_ENTER', 'ZONE_DWELL', 'ZONE_EXIT'])
    c_queued = count_visitors(['BILLING_QUEUE_JOIN'])
    c_purchased = count_visitors(['PURCHASE_PROXY'])
    c_exited = count_visitors(['EXIT'])

    stages_data = [
        ("entered", c_entered),
        ("browsed_zone", c_browsed),
        ("joined_queue", c_queued),
        ("completed_billing", c_purchased),
        ("exited", c_exited)
    ]

    stages = []
    drop_off_rates = {}
    
    for i, (name, count) in enumerate(stages_data):
        stages.append(FunnelStage(stage=name, count=count))
        if i > 0:
            prev_name, prev_count = stages_data[i-1]
            if prev_count > 0:
                drop_off = max(0.0, 1.0 - (count / prev_count))
            else:
                drop_off = 0.0
            drop_off_rates[f"{prev_name}_to_{name}"] = float(drop_off)

    return FunnelResponse(
        store_id=store_id,
        window=window,
        stages=stages,
        drop_off_rates=drop_off_rates,
    )

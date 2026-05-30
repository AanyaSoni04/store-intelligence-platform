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

from sqlalchemy.orm import Session

from store_intel.events.schemas import FunnelResponse

logger = logging.getLogger("store_intel")


def compute_funnel(db: Session, store_id: str, window: str) -> FunnelResponse:
    """
    Compute visitor funnel for a store within a time window.

    TODO: Implement SQL queries for each funnel stage.
    """
    raise NotImplementedError("Funnel computation not yet implemented")

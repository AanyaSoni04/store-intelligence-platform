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

from sqlalchemy.orm import Session

from store_intel.events.schemas import MetricsResponse

logger = logging.getLogger("store_intel")


def compute_metrics(db: Session, store_id: str, window: str) -> MetricsResponse:
    """
    Compute KPI snapshot for a store within a time window.

    TODO: Implement SQL queries for each metric.
    """
    raise NotImplementedError("Metric computation not yet implemented")


def parse_window(window: str) -> int:
    """
    Convert window string to seconds.

    TODO: Implement parsing for: 5m, 15m, 1h, 1d, 7d
    """
    # TODO: Implement window parsing
    mapping = {"5m": 300, "15m": 900, "1h": 3600, "1d": 86400, "7d": 604800}
    return mapping.get(window, 3600)

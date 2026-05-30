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

from sqlalchemy.orm import Session

from store_intel.events.schemas import HeatmapResponse

logger = logging.getLogger("store_intel")


def compute_heatmap(db: Session, store_id: str, window: str) -> HeatmapResponse:
    """
    Compute zone heatmap for a store within a time window.

    TODO: Implement SQL queries for zone visit counts and dwell times.
    """
    raise NotImplementedError("Heatmap computation not yet implemented")

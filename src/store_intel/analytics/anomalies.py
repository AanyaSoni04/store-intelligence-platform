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

from sqlalchemy.orm import Session

from store_intel.events.schemas import AnomalyResponse

logger = logging.getLogger("store_intel")


def detect_anomalies(
    db: Session,
    store_id: str,
    window: str,
    severity: str | None = None,
) -> AnomalyResponse:
    """
    Run all anomaly checks for a store within a time window.

    TODO: Implement each check function and aggregate results.
    """
    raise NotImplementedError("Anomaly detection not yet implemented")


def _check_unusual_dwell(db: Session, store_id: str, from_time, to_time) -> list:
    """TODO: Query ZONE_DWELL events where dwell_seconds > threshold."""
    return []


def _check_queue_buildup(db: Session, store_id: str, from_time, to_time) -> list:
    """TODO: Count active BILLING_QUEUE_JOIN without matching EXIT."""
    return []


def _check_empty_store(db: Session, store_id: str, from_time, to_time) -> list:
    """TODO: Check for time gaps with zero ENTRY events."""
    return []


def _check_high_abandonment(db: Session, store_id: str, from_time, to_time) -> list:
    """TODO: Compute abandonment rate and check against threshold."""
    return []

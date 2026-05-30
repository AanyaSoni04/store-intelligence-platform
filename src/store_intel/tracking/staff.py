"""
Staff exclusion logic.

Two-tier approach:
    Tier 1 (Behavioral): Flag visitors with continuous dwell > T_staff_threshold
    Tier 2 (Manual):     Admin API marks specific visitor_ids as staff

TODO: Implement StaffDetector with:
    - check_behavioral(visitor_id, total_dwell, db) → bool
    - mark_as_staff(visitor_id, db) → None
    - is_staff(visitor_id, db) → bool
"""

import logging

from sqlalchemy.orm import Session

from store_intel.db.models import Visitor

logger = logging.getLogger("store_intel")


class StaffDetector:
    """
    Detects and flags store staff to exclude from KPIs.

    TODO: Implement behavioral detection:
        - Track cumulative dwell time per visitor
        - Flag as staff if dwell exceeds threshold (default: 60 min)
    """

    def __init__(self, dwell_threshold_seconds: int = 3600):
        self.dwell_threshold = dwell_threshold_seconds

    def check_behavioral(self, visitor_id: str, total_dwell_seconds: float, db: Session) -> bool:
        """
        Check if a visitor should be flagged as staff based on dwell time.

        TODO: Implement:
            - If total_dwell_seconds > threshold → mark as staff
            - Update visitors.is_staff in the database
        """
        # TODO: Implement behavioral staff detection
        return False

    @staticmethod
    def mark_as_staff(visitor_id: str, db: Session) -> None:
        """
        Manually mark a visitor as staff.

        TODO: Implement:
            - Update visitors.is_staff = True
            - Log the action
        """
        visitor = db.query(Visitor).filter(Visitor.visitor_id == visitor_id).first()
        if visitor:
            visitor.is_staff = True
            db.commit()
            logger.info("Visitor marked as staff", extra={"visitor_id": visitor_id})

    @staticmethod
    def is_staff(visitor_id: str, db: Session) -> bool:
        """Check if a visitor is flagged as staff."""
        visitor = db.query(Visitor).filter(Visitor.visitor_id == visitor_id).first()
        return visitor.is_staff if visitor else False

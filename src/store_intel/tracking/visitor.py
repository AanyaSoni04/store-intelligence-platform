"""
Visitor identity manager.

Responsibilities:
    - Assign visitor_ids to new ByteTrack track_ids
    - Detect re-entry using time-gap + gate heuristic
    - Maintain track_id → visitor_id mapping

TODO: Implement VisitorManager with:
    - get_or_create(track_id, store_id) → visitor_id
    - check_reentry(entry_event, db_session) → existing visitor_id or None
    - cleanup_stale_tracks(max_age_frames)
"""

import logging
from uuid import uuid4

from sqlalchemy.orm import Session

logger = logging.getLogger("store_intel")


class VisitorManager:
    """
    Maps ByteTrack track_ids to persistent visitor_ids.

    TODO: Implement re-entry detection:
        - On new ENTRY event, check for recent EXIT at the same gate
        - If exactly one match within REENTRY_WINDOW → reuse visitor_id
        - Otherwise → create new visitor_id
    """

    def __init__(self, store_id: str, reentry_window_seconds: int = 300):
        self.store_id = store_id
        self.reentry_window = reentry_window_seconds
        self._track_to_visitor: dict[int, str] = {}

    def get_or_create(self, track_id: int) -> str:
        """
        Get existing visitor_id for a track, or create a new one.

        TODO: Integrate with re-entry detection before creating new IDs.
        """
        if track_id not in self._track_to_visitor:
            visitor_id = f"v_{uuid4().hex[:12]}"
            self._track_to_visitor[track_id] = visitor_id
            logger.debug(
                "New visitor assigned",
                extra={"track_id": track_id, "visitor_id": visitor_id},
            )
        return self._track_to_visitor[track_id]

    def check_reentry(self, gate_id: str, db: Session) -> str | None:
        """
        Check if a new entry is a re-entry of a recent visitor.

        TODO: Implement time-gap + gate heuristic:
            - Query recent EXIT events at the same gate within reentry_window
            - If exactly one match → return that visitor_id
            - Otherwise → return None
        """
        # TODO: Implement re-entry detection
        return None

    def remove_track(self, track_id: int) -> None:
        """Remove a track mapping when the track is lost."""
        self._track_to_visitor.pop(track_id, None)

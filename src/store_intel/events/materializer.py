"""
Event Materializer — per-track finite state machine.

Converts raw tracking data (track_id, centroid, zone hits) into
typed StoreEvent objects.

TODO: Implement the FSM with the following states:
    OUTSIDE → ENTERED → IN_ZONE → IN_QUEUE → EXITED
    Each state transition emits the corresponding event.

TODO: Implement dwell timer that emits ZONE_DWELL every 30 seconds.
TODO: Implement billing zone completion inference.
"""

import logging

from store_intel.events.schemas import StoreEvent

logger = logging.getLogger("store_intel")


class TrackState:
    """
    State machine for a single tracked person.

    TODO: Implement state transitions:
        - OUTSIDE → ENTERED (entry line crossing)
        - ENTERED → IN_ZONE (zone polygon hit)
        - IN_ZONE → IN_ZONE (different zone)
        - IN_ZONE → IN_QUEUE (billing zone hit)
        - * → EXITED (exit line crossing)
    """

    def __init__(self, track_id: int, store_id: str, camera_id: str):
        self.track_id = track_id
        self.store_id = store_id
        self.camera_id = camera_id
        self.state = "OUTSIDE"
        self.visitor_id: str | None = None
        self.current_zone: str | None = None
        self.zone_enter_time = None
        self.zones_visited: list[str] = []
        self.entry_time = None

    def update(self, centroid: tuple[float, float], timestamp, zone_hits: list[str]) -> list[StoreEvent]:
        """
        Process a new frame observation and emit any resulting events.

        TODO: Implement FSM transition logic here.

        Args:
            centroid: (x, y) position of the track centroid
            timestamp: current frame timestamp
            zone_hits: list of zone_ids the centroid is currently inside

        Returns:
            List of StoreEvent objects emitted by this state transition
        """
        # TODO: Implement state machine logic
        raise NotImplementedError("FSM state transitions not yet implemented")


class EventMaterializer:
    """
    Manages TrackState instances for all active tracks.

    TODO: Implement:
        - Track lifecycle management (create on first sight, cleanup on lost)
        - Delegate centroid + zone hits to per-track FSM
        - Collect and return emitted events
    """

    def __init__(self, store_id: str, camera_id: str):
        self.store_id = store_id
        self.camera_id = camera_id
        self.tracks: dict[int, TrackState] = {}

    def process_frame(
        self,
        tracked_objects: list[dict],
        timestamp,
    ) -> list[StoreEvent]:
        """
        Process all tracked objects in a single frame.

        TODO: Implement frame processing logic.

        Args:
            tracked_objects: list of {"track_id": int, "centroid": (x,y), "bbox": [...]}
            timestamp: frame timestamp

        Returns:
            List of events emitted across all tracks in this frame
        """
        # TODO: Implement frame processing
        raise NotImplementedError("Frame processing not yet implemented")

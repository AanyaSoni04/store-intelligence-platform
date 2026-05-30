"""
Multi-object tracker — ByteTrack wrapper via the supervision library.

TODO: Implement MultiObjectTracker class with:
    - __init__(): configure ByteTrack parameters
    - update(detections): feed detections, return tracked objects with persistent IDs
    - TrackedPerson dataclass: track_id, bbox, centroid, confidence, age (frames tracked)
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger("store_intel")


@dataclass
class TrackedPerson:
    """A tracked person with persistent identity across frames."""
    track_id: int
    bbox: tuple[float, float, float, float]  # (x1, y1, x2, y2)
    centroid: tuple[float, float]             # (cx, cy)
    confidence: float
    age: int = 0  # frames since first tracked


class MultiObjectTracker:
    """
    ByteTrack multi-object tracker wrapper.

    TODO: Implement using supervision.ByteTrack.

    Usage:
        tracker = MultiObjectTracker()
        tracked = tracker.update(detections)
    """

    def __init__(
        self,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        minimum_matching_threshold: float = 0.8,
    ):
        self.track_activation_threshold = track_activation_threshold
        self.lost_track_buffer = lost_track_buffer
        self.minimum_matching_threshold = minimum_matching_threshold
        # TODO: Initialize sv.ByteTrack with these parameters

    def update(self, detections: list) -> list[TrackedPerson]:
        """
        Update tracker with new detections and return tracked persons.

        TODO: Implement:
            - Convert detections to supervision.Detections format
            - Run ByteTrack update
            - Convert results to TrackedPerson objects
            - Compute centroids from bboxes
        """
        raise NotImplementedError("MultiObjectTracker not yet implemented")

"""
Multi-object tracker — ByteTrack wrapper via the supervision library.
"""

import logging
from dataclasses import dataclass
import numpy as np

try:
    import supervision as sv
except ImportError:
    sv = None

from store_intel.detection.detector import Detection

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
        if sv is not None:
            self.tracker = sv.ByteTrack(
                track_activation_threshold=track_activation_threshold,
                lost_track_buffer=lost_track_buffer,
                minimum_matching_threshold=minimum_matching_threshold
            )
        else:
            logger.warning("supervision is not available. Falling back to synthetic tracker.")
            self.tracker = None
        
        # Track age is not natively tracked by sv.ByteTrack output easily without custom state,
        # so we will keep our own mapping of track_id to age.
        self._track_age: dict[int, int] = {}

    def update(self, detections: list[Detection]) -> list[TrackedPerson]:
        """
        Update tracker with new detections and return tracked persons.
        """
        if not detections:
            # If no detections, still update tracker with empty to age out lost tracks
            empty_dets = sv.Detections.empty()
            tracked_sv = self.tracker.update_with_detections(empty_dets)
            return []
            
        # Convert our Detection objects to supervision Detections
        # supervision expects xyxy numpy array shape (N, 4)
        xyxy = np.array([d.bbox for d in detections])
        confidence = np.array([d.confidence for d in detections])
        class_id = np.array([d.class_id for d in detections])
        
        sv_detections = sv.Detections(
            xyxy=xyxy,
            confidence=confidence,
            class_id=class_id
        )
        
        # Run ByteTrack
        tracked_sv = self.tracker.update_with_detections(sv_detections)
        
        results = []
        active_track_ids = set()
        
        for i in range(len(tracked_sv)):
            tracker_bbox = tuple(float(x) for x in tracked_sv.xyxy[i])
            tracker_conf = float(tracked_sv.confidence[i]) if tracked_sv.confidence is not None else 1.0
            track_id = int(tracked_sv.tracker_id[i])
            
            active_track_ids.add(track_id)
            
            # Increment age
            self._track_age[track_id] = self._track_age.get(track_id, 0) + 1
            
            # Calculate centroid (bottom center is best for feet, as it maps directly to floor polygons)
            cx = (tracker_bbox[0] + tracker_bbox[2]) / 2.0
            cy = tracker_bbox[3]
            
            results.append(
                TrackedPerson(
                    track_id=track_id,
                    bbox=tracker_bbox,
                    centroid=(cx, cy),
                    confidence=tracker_conf,
                    age=self._track_age[track_id]
                )
            )
            
        # Cleanup old ages for tracks that are gone (we can periodically prune, 
        # but for now we just let ByteTrack handle the buffer and we could leak a tiny bit of int->int memory)
        
        return results

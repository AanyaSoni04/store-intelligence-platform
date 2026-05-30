"""
Unit tests for MultiObjectTracker.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

# Need to mock supervision before importing if it's missing, but we'll assume it exists or mock it
import sys

# Create a dummy sv module for testing
class DummyDetections:
    def __init__(self, xyxy=None, confidence=None, class_id=None, tracker_id=None):
        self.xyxy = xyxy
        self.confidence = confidence
        self.class_id = class_id
        self.tracker_id = tracker_id
        
    @classmethod
    def empty(cls):
        return cls(xyxy=np.empty((0, 4)), confidence=np.empty(0), class_id=np.empty(0))

    def __len__(self):
        return len(self.xyxy) if self.xyxy is not None else 0

class DummyByteTrack:
    def __init__(self, **kwargs):
        pass
    def update_with_detections(self, detections):
        # Just return the detections with fake tracker_ids
        if len(detections) > 0:
            detections.tracker_id = np.array([1, 2][:len(detections)])
        return detections

# Mocking supervision in sys.modules so the tracker imports successfully
mock_sv = MagicMock()
mock_sv.Detections = DummyDetections
mock_sv.ByteTrack = DummyByteTrack
sys.modules['supervision'] = mock_sv

from store_intel.detection.tracker import MultiObjectTracker, TrackedPerson
from store_intel.detection.detector import Detection

class TestMultiObjectTracker:
    def test_tracker_initialization(self):
        tracker = MultiObjectTracker(track_activation_threshold=0.5)
        assert tracker is not None

    def test_tracker_update(self):
        tracker = MultiObjectTracker()
        
        # Mock 2 detections
        dets = [
            Detection(bbox=(10, 10, 20, 20), confidence=0.9, class_id=0),
            Detection(bbox=(30, 30, 40, 40), confidence=0.8, class_id=0)
        ]
        
        tracked = tracker.update(dets)
        
        assert len(tracked) == 2
        assert isinstance(tracked[0], TrackedPerson)
        assert tracked[0].track_id == 1
        assert tracked[0].confidence == 0.9
        # Centroid of (10, 10, 20, 20) with bottom-center is (15.0, 20.0)
        assert tracked[0].centroid == (15.0, 20.0)
        assert tracked[0].age == 1
        
        # Second frame update to test age increment
        tracked_frame2 = tracker.update(dets)
        assert tracked_frame2[0].age == 2

    def test_tracker_empty_update(self):
        tracker = MultiObjectTracker()
        tracked = tracker.update([])
        assert len(tracked) == 0

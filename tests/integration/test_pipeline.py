"""
Integration tests for the DetectionPipeline.
"""
import os
import json
from pathlib import Path
import pytest
import numpy as np

# Mocking components so we don't actually load ML models
from unittest.mock import MagicMock, patch

from store_intel.detection.pipeline import DetectionPipeline
from store_intel.events.schemas import EventType

@pytest.fixture
def mock_cv2(monkeypatch):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    
    # We will simulate 10 frames
    frame_idx = 0
    def read_side_effect():
        nonlocal frame_idx
        if frame_idx < 10:
            frame_idx += 1
            return True, np.zeros((10, 10, 3))
        return False, None
        
    mock_cap.read.side_effect = read_side_effect
    mock_cap.get.return_value = 30.0  # 30 fps
    
    mock_cv2 = MagicMock()
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_PROP_FPS = 5
    
    monkeypatch.setattr("store_intel.detection.pipeline.cv2", mock_cv2)
    return mock_cv2

@pytest.fixture
def mock_components(monkeypatch):
    # Mock Detector
    mock_detector = MagicMock()
    mock_detector.detect.return_value = ["dummy_detection"]
    
    # Mock Tracker
    mock_tracker = MagicMock()
    mock_person = MagicMock()
    mock_person.track_id = 1
    mock_person.centroid = (5.0, 5.0)
    mock_tracker.update.return_value = [mock_person]
    
    # Mock ZoneManager
    mock_zm = MagicMock()
    # Mock it so that the person is in "electronics" for frames 1-5, and out for 6-10
    call_idx = 0
    def check_zones_side_effect(centroid):
        nonlocal call_idx
        call_idx += 1
        if call_idx <= 5:
            return ["electronics"]
        return []
    mock_zm.check_zones.side_effect = check_zones_side_effect
    
    monkeypatch.setattr("store_intel.detection.pipeline.PersonDetector", lambda: mock_detector)
    monkeypatch.setattr("store_intel.detection.pipeline.MultiObjectTracker", lambda: mock_tracker)
    monkeypatch.setattr("store_intel.detection.pipeline.ZoneManager", lambda config: mock_zm)


class TestDetectionPipeline:
    def test_pipeline_cam1_zone_events(self, mock_cv2, mock_components, tmp_path):
        test_path = tmp_path / "generated_events.json"
        
        with patch("store_intel.detection.pipeline.Path") as mock_path_cls:
            mock_path_instance = MagicMock()
            mock_path_instance.__truediv__.return_value = test_path
            mock_path_instance.parent = test_path.parent
            mock_path_cls.return_value = test_path
            
            pipeline = DetectionPipeline(
                video_source="dummy.mp4",
                store_id="store_1",
                camera_id="CAM1",
                target_fps=30
            )
            
            event_count = pipeline.run()
            
            assert event_count == 2
            
            # Verify JSON was written
            assert test_path.exists()
            with open(test_path, "r") as f:
                data = json.load(f)
                
            assert len(data) == 2
            assert data[0]["event_type"] == EventType.ZONE_ENTER.value
            assert data[1]["event_type"] == EventType.ZONE_EXIT.value

    def test_pipeline_cam3_mapping(self, mock_cv2, mock_components, tmp_path):
        test_path = tmp_path / "generated_events.json"
        
        with patch("store_intel.detection.pipeline.Path") as mock_path_cls:
            mock_path_cls.return_value = test_path
            
            pipeline = DetectionPipeline(
                video_source="dummy.mp4",
                store_id="store_1",
                camera_id="CAM3",
                target_fps=30
            )
            
            pipeline.run()
            
            with open(test_path, "r") as f:
                data = json.load(f)
                
            assert data[0]["event_type"] == "ENTRY"
            assert data[1]["event_type"] == "EXIT"

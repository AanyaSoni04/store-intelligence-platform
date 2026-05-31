import pytest
from datetime import datetime, timezone
from store_intel.detection.pipeline import DetectionPipeline
from store_intel.events.schemas import StoreEvent, EventType

def test_pipeline_group_clustering():
    pipeline = DetectionPipeline(video_source="mock.mp4", store_id="test_store", camera_id="cam_001", zone_config="configs/zones/cam_001.json")
    
    # Create fake entry events
    t = datetime.now(timezone.utc)
    ev1 = StoreEvent(event_id="1", store_id="1", camera_id="1", visitor_id="v1", event_type=EventType.ENTRY, timestamp=t, confidence=1.0, metadata={})
    ev1._temp_track_id = 1
    
    ev2 = StoreEvent(event_id="2", store_id="1", camera_id="1", visitor_id="v2", event_type=EventType.ENTRY, timestamp=t, confidence=1.0, metadata={})
    ev2._temp_track_id = 2
    
    ev3 = StoreEvent(event_id="3", store_id="1", camera_id="1", visitor_id="v3", event_type=EventType.ENTRY, timestamp=t, confidence=1.0, metadata={})
    ev3._temp_track_id = 3
    
    centroids = {
        1: (100, 100),
        2: (120, 120),  # Close to 1
        3: (800, 800)   # Far away
    }
    
    events = [ev1, ev2, ev3]
    pipeline._cluster_entry_events(events, centroids)
    
    assert ev1.metadata["group_size"] == 2
    assert ev2.metadata["group_size"] == 2
    assert ev3.metadata["group_size"] == 1

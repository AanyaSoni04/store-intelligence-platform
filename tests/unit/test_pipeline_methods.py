import pytest
from unittest.mock import MagicMock
from store_intel.detection.pipeline import DetectionPipeline
from store_intel.events.schemas import StoreEvent, EventType
from datetime import datetime, timezone

def test_pipeline_methods():
    pipeline3 = DetectionPipeline(video_source="mock", store_id="test_store", camera_id="CAM3", zone_config="configs/zones/cam_001.json")
    pipeline5 = DetectionPipeline(video_source="mock", store_id="test_store", camera_id="CAM5", zone_config="configs/zones/cam_001.json")
    
    # Test _map_events_for_camera CAM3
    t = datetime.now(timezone.utc)
    ev_zone_enter = StoreEvent(event_id="1", store_id="1", camera_id="CAM3", visitor_id="v1", event_type=EventType.ZONE_ENTER, timestamp=t, metadata={"zone_id": "entrance"}, confidence=1.0)
    ev_zone_exit = StoreEvent(event_id="2", store_id="1", camera_id="CAM3", visitor_id="v1", event_type=EventType.ZONE_EXIT, timestamp=t, metadata={"zone_id": "entrance"}, confidence=1.0)
    
    mapped3 = pipeline3._map_events_for_camera([ev_zone_enter, ev_zone_exit])
    
    types_str3 = [t.value if hasattr(t, 'value') else str(t) for t in [e.event_type for e in mapped3]]
    assert 'ENTRY' in types_str3
    assert 'EXIT' in types_str3
    
    # Test CAM5
    ev_dwell = StoreEvent(event_id="3", store_id="1", camera_id="CAM5", visitor_id="v1", event_type=EventType.ZONE_ENTER, timestamp=t, metadata={"zone_id": "billing_queue"}, confidence=1.0)
    mapped5 = pipeline5._map_events_for_camera([ev_dwell])
    types_str5 = [t.value if hasattr(t, 'value') else str(t) for t in [e.event_type for e in mapped5]]
    assert 'BILLING_QUEUE_JOIN' in types_str5
    
    # Test telemetry
    pipeline3.socket_client = MagicMock()
    pipeline3.zone_manager = MagicMock()
    pipeline3.zone_manager.zones = {}
    
    pipeline3._emit_telemetry({1, 2, 3})
    
    # Test parsing fps
    # It won't fail

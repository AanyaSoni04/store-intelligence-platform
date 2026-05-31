import pytest
import json
from datetime import datetime, timezone, timedelta
from store_intel.db.crud import insert_event, get_visitor
from store_intel.events.schemas import StoreEvent, EventType

def test_cross_camera_session_merge(db_session, sample_store):
    t_base = datetime.now(timezone.utc)
    store_id = sample_store.store_id
    
    # Visitor exits from CAM1
    exit_event = StoreEvent(
        event_id="evt_exit_1",
        store_id=store_id,
        camera_id="cam_001",
        visitor_id="v_orig",
        event_type=EventType.EXIT,
        timestamp=t_base,
        confidence=1.0
    )
    insert_event(db_session, exit_event)
    
    # Visitor enters CAM2 10 seconds later
    t_entry = t_base + timedelta(seconds=10)
    entry_event = StoreEvent(
        event_id="evt_entry_2",
        store_id=store_id,
        camera_id="cam_002",
        visitor_id="v_new",
        event_type=EventType.ENTRY,
        timestamp=t_entry,
        confidence=1.0
    )
    db_entry = insert_event(db_session, entry_event)
    
    # Assert the visitor ID was rewritten
    assert db_entry.visitor_id == "v_orig"
    assert db_entry.event_type == EventType.REENTRY.value
    assert json.loads(db_entry.metadata_json).get("cross_camera_merge") is True
    
    # Check the DB mapping
    v_new = get_visitor(db_session, "v_new")
    assert v_new.merged_into == "v_orig"
    
    # Subsequent event from CAM2 using v_new should be rewritten to v_orig
    t_dwell = t_entry + timedelta(seconds=5)
    dwell_event = StoreEvent(
        event_id="evt_dwell_3",
        store_id=store_id,
        camera_id="cam_002",
        visitor_id="v_new", # Pipeline still thinks it's v_new
        event_type=EventType.ZONE_DWELL,
        timestamp=t_dwell,
        confidence=1.0
    )
    db_dwell = insert_event(db_session, dwell_event)
    
    assert db_dwell.visitor_id == "v_orig"

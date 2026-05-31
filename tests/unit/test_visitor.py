"""
Unit tests for VisitorManager.
"""
from datetime import datetime, timezone, timedelta
from store_intel.tracking.visitor import VisitorManager, STAFF_SCORE_THRESHOLD


class TestVisitorManager:
    """Tests for visitor identity management and staff heuristics."""

    def test_new_track_gets_id(self):
        vm = VisitorManager(store_id="test_store")
        state = vm.get_or_create(track_id=1, timestamp=datetime.now(timezone.utc))[0]
        assert state.visitor_id.startswith("v_")

    def test_same_track_same_id(self):
        vm = VisitorManager(store_id="test_store")
        t = datetime.now(timezone.utc)
        state1 = vm.get_or_create(track_id=1, timestamp=t)[0]
        state2 = vm.get_or_create(track_id=1, timestamp=t)[0]
        assert state1.visitor_id == state2.visitor_id

    def test_different_tracks_different_ids(self):
        vm = VisitorManager(store_id="test_store")
        t = datetime.now(timezone.utc)
        state1 = vm.get_or_create(track_id=1, timestamp=t)[0]
        state2 = vm.get_or_create(track_id=2, timestamp=t)[0]
        assert state1.visitor_id != state2.visitor_id

    def test_remove_track(self):
        vm = VisitorManager(store_id="test_store")
        t = datetime.now(timezone.utc)
        vm.get_or_create(track_id=1, timestamp=t)
        vm.remove_track(track_id=1, timestamp=t)
        state_new = vm.get_or_create(track_id=1, timestamp=t + timedelta(seconds=1000))[0]
        assert state_new.visitor_id.startswith("v_")

    def test_zone_entry_exit_events(self):
        vm = VisitorManager(store_id="test_store")
        t1 = datetime.now(timezone.utc)
        
        # Enter zone
        events1 = vm.process_zone_hits(1, "cam1", ["electronics"], t1)
        assert len(events1) == 1
        assert events1[0].event_type == "ZONE_ENTER"
        assert events1[0].metadata["zone_id"] == "electronics"
        
        # Stay in zone (no new events)
        t2 = t1 + timedelta(seconds=10)
        events2 = vm.process_zone_hits(1, "cam1", ["electronics"], t2)
        assert len(events2) == 0
        
        # Exit zone
        t3 = t2 + timedelta(seconds=10)
        events3 = vm.process_zone_hits(1, "cam1", [], t3)
        assert len(events3) == 1
        assert events3[0].event_type == "ZONE_EXIT"
        assert events3[0].metadata["zone_id"] == "electronics"
        assert events3[0].metadata["dwell_seconds"] == 20.0

    def test_staff_scoring_heuristic(self):
        vm = VisitorManager(store_id="test_store")
        t1 = datetime.now(timezone.utc)
        
        # Originates from staff zone (+50)
        vm.process_zone_hits(1, "cam1", ["stockroom"], t1)
        state = vm.get_or_create(1, t1)[0]
        assert state.staff_score == 50
        assert not state.is_staff
        
        # Enters staff zone again (+30)
        t2 = t1 + timedelta(seconds=10)
        vm.process_zone_hits(1, "cam1", [], t2) # leave
        t3 = t2 + timedelta(seconds=10)
        vm.process_zone_hits(1, "cam1", ["behind_counter"], t3) # enter
        assert state.staff_score == 80
        
        # Enters one more time to push over threshold
        t4 = t3 + timedelta(seconds=10)
        vm.process_zone_hits(1, "cam1", [], t4)
        t5 = t4 + timedelta(seconds=10)
        vm.process_zone_hits(1, "cam1", ["stockroom"], t5)
        
        assert state.staff_score == 110
        assert state.is_staff is True

    def test_reentry_deduplication(self):
        vm = VisitorManager(store_id="test_store")
        t1 = datetime.now(timezone.utc)
        
        # 1. Person enters
        events = vm.process_zone_hits(1, "cam1", ["electronics"], t1)
        assert len(events) == 1
        state_original = vm.get_or_create(1, t1)[0]
        vid_original = state_original.visitor_id
        
        # 2. Person leaves camera view
        t2 = t1 + timedelta(seconds=10)
        vm.remove_track(1, t2)
        
        # Track is removed from active states but lives in exited cache
        assert 1 not in vm._states
        assert vid_original in vm.exited_visitors
        
        # 3. Person returns 200 seconds later (within 300s window) with new track_id
        t3 = t2 + timedelta(seconds=200)
        events_reentry = vm.process_zone_hits(2, "cam1", ["electronics"], t3)
        
        state_reentry = vm.get_or_create(2, t3)[0]
        
        # Assert ID is preserved
        assert state_reentry.visitor_id == vid_original
        
        event_types = [e.event_type.value if hasattr(e.event_type, 'value') else e.event_type for e in events_reentry]
        assert "REENTRY" in event_types
        
        # 4. Person leaves again
        t4 = t3 + timedelta(seconds=10)
        vm.remove_track(2, t4)
        
        # 5. Person returns 400 seconds later (outside 300s window)
        t5 = t4 + timedelta(seconds=400)
        events_late = vm.process_zone_hits(3, "cam1", ["electronics"], t5)
        
        state_late = vm.get_or_create(3, t5)[0]
        
        # Assert ID is NOT preserved
        assert state_late.visitor_id != vid_original
        assert "REENTRY" not in [e.event_type for e in events_late]

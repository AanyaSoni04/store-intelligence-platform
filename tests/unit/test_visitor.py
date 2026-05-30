"""
Unit tests for VisitorManager.
"""
from datetime import datetime, timezone, timedelta
from store_intel.tracking.visitor import VisitorManager, STAFF_SCORE_THRESHOLD


class TestVisitorManager:
    """Tests for visitor identity management and staff heuristics."""

    def test_new_track_gets_id(self):
        vm = VisitorManager(store_id="test_store")
        state = vm.get_or_create(track_id=1)
        assert state.visitor_id.startswith("v_")

    def test_same_track_same_id(self):
        vm = VisitorManager(store_id="test_store")
        state1 = vm.get_or_create(track_id=1)
        state2 = vm.get_or_create(track_id=1)
        assert state1.visitor_id == state2.visitor_id

    def test_different_tracks_different_ids(self):
        vm = VisitorManager(store_id="test_store")
        state1 = vm.get_or_create(track_id=1)
        state2 = vm.get_or_create(track_id=2)
        assert state1.visitor_id != state2.visitor_id

    def test_remove_track(self):
        vm = VisitorManager(store_id="test_store")
        vm.get_or_create(track_id=1)
        vm.remove_track(track_id=1)
        state_new = vm.get_or_create(track_id=1)
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
        state = vm.get_or_create(1)
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

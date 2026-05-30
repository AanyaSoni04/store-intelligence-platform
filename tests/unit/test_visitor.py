"""
Unit tests for VisitorManager.

TODO: Implement tests when visitor tracking logic is built:
    - test_new_track_gets_unique_id
    - test_same_track_returns_same_id
    - test_reentry_detection
    - test_no_reentry_after_window_expires
    - test_remove_track_cleanup
"""

from store_intel.tracking.visitor import VisitorManager


class TestVisitorManager:
    """Tests for visitor identity management."""

    def test_new_track_gets_id(self):
        """A new track_id should be assigned a visitor_id."""
        vm = VisitorManager(store_id="test_store")
        vid = vm.get_or_create(track_id=1)
        assert vid.startswith("v_")

    def test_same_track_same_id(self):
        """The same track_id should always return the same visitor_id."""
        vm = VisitorManager(store_id="test_store")
        vid1 = vm.get_or_create(track_id=1)
        vid2 = vm.get_or_create(track_id=1)
        assert vid1 == vid2

    def test_different_tracks_different_ids(self):
        """Different track_ids should get different visitor_ids."""
        vm = VisitorManager(store_id="test_store")
        vid1 = vm.get_or_create(track_id=1)
        vid2 = vm.get_or_create(track_id=2)
        assert vid1 != vid2

    def test_remove_track(self):
        """Removing a track should clear the mapping."""
        vm = VisitorManager(store_id="test_store")
        vm.get_or_create(track_id=1)
        vm.remove_track(track_id=1)
        # Next call should create a new visitor_id
        vid_new = vm.get_or_create(track_id=1)
        assert vid_new.startswith("v_")

    # TODO: Add re-entry detection tests once check_reentry is implemented

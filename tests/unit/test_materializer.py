"""
Unit tests for EventMaterializer (FSM).

TODO: Implement tests when FSM logic is built:
    - test_entry_event_on_line_crossing
    - test_exit_event_on_line_crossing
    - test_zone_enter_on_polygon_hit
    - test_zone_exit_on_polygon_leave
    - test_zone_dwell_after_threshold
    - test_billing_queue_join
    - test_billing_queue_abandon
    - test_multiple_zone_transitions
    - test_no_events_when_stationary
"""


class TestTrackState:
    """Tests for individual track state machine."""

    def test_placeholder(self):
        """Placeholder — remove when FSM is implemented."""
        # TODO: Replace with real FSM tests
        assert True


class TestEventMaterializer:
    """Tests for the event materializer that manages multiple tracks."""

    def test_placeholder(self):
        """Placeholder — remove when materializer is implemented."""
        # TODO: Replace with real materializer tests
        assert True

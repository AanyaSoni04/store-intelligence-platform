"""
Unit tests for analytics metrics computation.

TODO: Implement tests when compute_metrics is built:
    - test_unique_visitors_count
    - test_conversion_rate_calculation
    - test_avg_dwell_time
    - test_queue_depth
    - test_abandonment_rate
    - test_staff_excluded_from_metrics
    - test_empty_store_returns_zeros
    - test_window_filtering
"""

from store_intel.analytics.metrics import parse_window


class TestMetrics:
    """Tests for KPI computation."""

    def test_parse_window_5m(self):
        assert parse_window("5m") == 300

    def test_parse_window_1h(self):
        assert parse_window("1h") == 3600

    def test_parse_window_1d(self):
        assert parse_window("1d") == 86400

    def test_parse_window_default(self):
        """Unknown window should default to 1h."""
        assert parse_window("unknown") == 3600

    # TODO: Add metric computation tests once compute_metrics is implemented

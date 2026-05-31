"""
Unit tests for analytics metrics computation.
"""

from store_intel.analytics.metrics import parse_window, compute_metrics
from store_intel.analytics.funnel import compute_funnel
from store_intel.analytics.heatmap import compute_heatmap


class TestMetrics:
    """Tests for KPI computation."""

    def test_parse_window_5m(self):
        assert parse_window("5m") == 300

    def test_parse_window_1h(self):
        assert parse_window("1h") == 3600

    def test_parse_window_1d(self):
        assert parse_window("1d") == 86400

    def test_parse_window_default(self):
        assert parse_window("unknown") == 3600

    def test_compute_metrics_empty(self, db_session, sample_store):
        metrics = compute_metrics(db_session, sample_store.store_id, "1h")
        assert metrics.unique_visitors == 0
        assert metrics.conversion_rate == 0.0
        assert metrics.avg_dwell_seconds == 0.0
        assert metrics.queue_depth == 0
        assert metrics.abandonment_rate == 0.0

    def test_compute_funnel_empty(self, db_session, sample_store):
        funnel = compute_funnel(db_session, sample_store.store_id, "1h")
        assert len(funnel.stages) == 5
        assert all(s.count == 0 for s in funnel.stages)
        assert len(funnel.drop_off_rates) == 4
        assert all(v == 0.0 for v in funnel.drop_off_rates.values())

    def test_compute_heatmap_empty(self, db_session, sample_store):
        heatmap = compute_heatmap(db_session, sample_store.store_id, "1h")
        assert len(heatmap.zones) == 0

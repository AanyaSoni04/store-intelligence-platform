"""
Unit tests for anomalies computation.
"""

from store_intel.analytics.anomalies import detect_anomalies


class TestAnomalyDetection:
    """Tests for anomaly detection logic."""

    def test_empty_store_stale_feed(self, db_session, sample_store):
        # Empty store should not alert stale feed unless it had previous events
        response = detect_anomalies(db_session, sample_store.store_id, "1h")
        assert len(response.anomalies) == 0


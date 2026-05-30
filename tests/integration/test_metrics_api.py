"""
Integration tests for analytics API endpoints.

Tests the full path: seeded data → HTTP request → computed response.

TODO: Implement once analytics engines are built:
    - test_metrics_with_seeded_data
    - test_funnel_stages_correct
    - test_heatmap_zone_counts
    - test_anomalies_detected
    - test_window_filtering
    - test_staff_excluded
"""


class TestMetricsAPI:
    """Integration tests for GET /stores/{id}/metrics."""

    def test_metrics_returns_200(self, client, sample_store):
        """Metrics endpoint should return 200 with zeroed values for empty store."""
        response = client.get(f"/stores/{sample_store.store_id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["store_id"] == sample_store.store_id
        assert data["unique_visitors"] == 0

    def test_metrics_window_param(self, client, sample_store):
        """Metrics endpoint should accept window parameter."""
        response = client.get(f"/stores/{sample_store.store_id}/metrics?window=1d")
        assert response.status_code == 200
        assert response.json()["window"] == "1d"


class TestFunnelAPI:
    """Integration tests for GET /stores/{id}/funnel."""

    def test_funnel_returns_200(self, client, sample_store):
        response = client.get(f"/stores/{sample_store.store_id}/funnel")
        assert response.status_code == 200
        assert response.json()["store_id"] == sample_store.store_id


class TestHeatmapAPI:
    """Integration tests for GET /stores/{id}/heatmap."""

    def test_heatmap_returns_200(self, client, sample_store):
        response = client.get(f"/stores/{sample_store.store_id}/heatmap")
        assert response.status_code == 200


class TestAnomaliesAPI:
    """Integration tests for GET /stores/{id}/anomalies."""

    def test_anomalies_returns_200(self, client, sample_store):
        response = client.get(f"/stores/{sample_store.store_id}/anomalies")
        assert response.status_code == 200


class TestHealthAPI:
    """Integration tests for GET /health."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["db"] == "connected"
        assert "version" in data

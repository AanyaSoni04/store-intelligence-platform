"""
Integration tests for analytics API endpoints.
"""


class TestMetricsAPI:
    """Integration tests for GET /stores/{id}/metrics."""

    def test_metrics_returns_200(self, client, sample_store):
        response = client.get(f"/stores/{sample_store.store_id}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["store_id"] == sample_store.store_id
        assert data["unique_visitors"] >= 0
        assert "conversion_rate" in data
        assert "avg_dwell_seconds" in data
        assert "queue_depth" in data
        assert "abandonment_rate" in data

    def test_metrics_window_param(self, client, sample_store):
        response = client.get(f"/stores/{sample_store.store_id}/metrics?window=1d")
        assert response.status_code == 200
        assert response.json()["window"] == "1d"


class TestFunnelAPI:
    """Integration tests for GET /stores/{id}/funnel."""

    def test_funnel_returns_200(self, client, sample_store):
        response = client.get(f"/stores/{sample_store.store_id}/funnel")
        assert response.status_code == 200
        data = response.json()
        assert data["store_id"] == sample_store.store_id
        assert len(data["stages"]) == 5


class TestHeatmapAPI:
    """Integration tests for GET /stores/{id}/heatmap."""

    def test_heatmap_returns_200(self, client, sample_store):
        response = client.get(f"/stores/{sample_store.store_id}/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data


class TestAnomaliesAPI:
    """Integration tests for GET /stores/{id}/anomalies."""

    def test_anomalies_returns_200(self, client, sample_store):
        response = client.get(f"/stores/{sample_store.store_id}/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data


class TestHealthAPI:
    """Integration tests for GET /health."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["db"] == "connected"
        assert "version" in data

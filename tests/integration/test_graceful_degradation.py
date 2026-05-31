from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy.exc import OperationalError
import sqlite3

from store_intel.main import app

client = TestClient(app)

def test_sqlalchemy_operational_error_returns_503():
    with patch("store_intel.api.metrics.compute_metrics") as mock_compute:
        mock_compute.side_effect = OperationalError("mock statement", "mock params", "mock orig")
        response = client.get("/stores/test_store/metrics?window=1h")
        assert response.status_code == 503
        assert response.json() == {"detail": "Service Unavailable: Database connection failed."}

def test_sqlite3_operational_error_returns_503():
    with patch("store_intel.api.metrics.compute_metrics") as mock_compute:
        mock_compute.side_effect = sqlite3.OperationalError("database is locked")
        response = client.get("/stores/test_store/metrics?window=1h")
        assert response.status_code == 503
        assert response.json() == {"detail": "Service Unavailable: Database connection failed."}

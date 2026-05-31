import pytest
from fastapi.testclient import TestClient

def test_mark_as_staff_success(client: TestClient, sample_store, sample_visitor):
    """Test marking a valid visitor as staff."""
    response = client.post(f"/stores/{sample_store.store_id}/visitors/{sample_visitor.visitor_id}/staff")
    assert response.status_code == 200
    data = response.json()
    assert data["is_staff"] is True
    assert data["visitor_id"] == sample_visitor.visitor_id

def test_mark_as_staff_not_found(client: TestClient, sample_store):
    """Test marking a non-existent visitor returns 404."""
    response = client.post(f"/stores/{sample_store.store_id}/visitors/nonexistent/staff")
    assert response.status_code == 404

"""
Integration tests for the event ingest API.

Tests the full path: HTTP request → validation → DB write → response.
"""

import json
from datetime import datetime, timezone


class TestIngestAPI:
    """Integration tests for POST /events/ingest."""

    def test_ingest_single_event(self, client, sample_store):
        """Ingesting a single valid event should return 202 with accepted=1."""
        payload = {
            "events": [
                {
                    "store_id": sample_store.store_id,
                    "camera_id": "cam_001",
                    "visitor_id": "v_new_001",
                    "event_type": "ENTRY",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.92,
                    "metadata": {"gate_id": "main_entrance"},
                }
            ]
        }
        response = client.post("/events/ingest", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["accepted"] == 1
        assert data["rejected"] == 0

    def test_ingest_batch(self, client, sample_store):
        """Ingesting multiple events should process all of them."""
        events = [
            {
                "store_id": sample_store.store_id,
                "camera_id": "cam_001",
                "visitor_id": f"v_batch_{i}",
                "event_type": "ENTRY",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence": 0.9,
                "metadata": {},
            }
            for i in range(5)
        ]
        response = client.post("/events/ingest", json={"events": events})
        assert response.status_code == 202
        assert response.json()["accepted"] == 5

    def test_ingest_invalid_event_type(self, client, sample_store):
        """An event with an invalid type should be rejected at validation."""
        payload = {
            "events": [
                {
                    "store_id": sample_store.store_id,
                    "camera_id": "cam_001",
                    "visitor_id": "v_001",
                    "event_type": "INVALID",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,
                }
            ]
        }
        response = client.post("/events/ingest", json=payload)
        assert response.status_code == 422  # Pydantic validation error

    def test_ingest_empty_batch(self, client):
        """An empty batch should be accepted with 0 events."""
        response = client.post("/events/ingest", json={"events": []})
        assert response.status_code == 202
        assert response.json()["accepted"] == 0

    # TODO: Test partial batch failure (mix of valid and invalid events)
    # TODO: Test idempotency (duplicate event_id handling)

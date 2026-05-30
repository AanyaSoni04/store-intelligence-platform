"""
Unit tests for Pydantic event schemas.

Tests:
    - Valid event creation
    - Event type validation
    - Confidence bounds validation
    - Batch size limit
    - Default event_id generation
    - Serialization roundtrip
"""

import pytest
from datetime import datetime, timezone

from store_intel.events.schemas import StoreEvent, EventType, EventBatch


class TestStoreEvent:
    """Tests for the StoreEvent Pydantic model."""

    def test_valid_event_creation(self):
        """A valid event should be created without errors."""
        event = StoreEvent(
            store_id="store_001",
            camera_id="cam_001",
            visitor_id="v_001",
            event_type=EventType.ENTRY,
            timestamp=datetime.now(timezone.utc),
            confidence=0.92,
            metadata={"gate_id": "main_entrance"},
        )
        assert event.store_id == "store_001"
        assert event.event_type == EventType.ENTRY
        assert event.event_id  # auto-generated

    def test_auto_generated_event_id(self):
        """event_id should be auto-generated if not provided."""
        e1 = StoreEvent(
            store_id="s", camera_id="c", visitor_id="v",
            event_type=EventType.EXIT, timestamp=datetime.now(timezone.utc),
            confidence=0.5,
        )
        e2 = StoreEvent(
            store_id="s", camera_id="c", visitor_id="v",
            event_type=EventType.EXIT, timestamp=datetime.now(timezone.utc),
            confidence=0.5,
        )
        assert e1.event_id != e2.event_id

    def test_confidence_lower_bound(self):
        """Confidence below 0.0 should raise validation error."""
        with pytest.raises(Exception):
            StoreEvent(
                store_id="s", camera_id="c", visitor_id="v",
                event_type=EventType.ENTRY, timestamp=datetime.now(timezone.utc),
                confidence=-0.1,
            )

    def test_confidence_upper_bound(self):
        """Confidence above 1.0 should raise validation error."""
        with pytest.raises(Exception):
            StoreEvent(
                store_id="s", camera_id="c", visitor_id="v",
                event_type=EventType.ENTRY, timestamp=datetime.now(timezone.utc),
                confidence=1.5,
            )

    def test_all_event_types(self):
        """All 8 event types should be valid."""
        for et in EventType:
            event = StoreEvent(
                store_id="s", camera_id="c", visitor_id="v",
                event_type=et, timestamp=datetime.now(timezone.utc),
                confidence=0.5,
            )
            assert event.event_type == et

    def test_invalid_event_type(self):
        """Invalid event type string should raise validation error."""
        with pytest.raises(Exception):
            StoreEvent(
                store_id="s", camera_id="c", visitor_id="v",
                event_type="INVALID_TYPE",
                timestamp=datetime.now(timezone.utc),
                confidence=0.5,
            )

    def test_default_metadata(self):
        """Metadata should default to empty dict."""
        event = StoreEvent(
            store_id="s", camera_id="c", visitor_id="v",
            event_type=EventType.ENTRY, timestamp=datetime.now(timezone.utc),
            confidence=0.5,
        )
        assert event.metadata == {}

    def test_serialization_roundtrip(self):
        """Event should survive JSON serialization and deserialization."""
        event = StoreEvent(
            store_id="store_001", camera_id="cam_001", visitor_id="v_001",
            event_type=EventType.ZONE_ENTER, timestamp=datetime(2026, 5, 30, tzinfo=timezone.utc),
            confidence=0.88,
            metadata={"zone_id": "electronics"},
        )
        json_str = event.model_dump_json()
        restored = StoreEvent.model_validate_json(json_str)
        assert restored.event_id == event.event_id
        assert restored.metadata["zone_id"] == "electronics"


class TestEventBatch:
    """Tests for the EventBatch model."""

    def test_valid_batch(self):
        """A batch with valid events should be created."""
        events = [
            StoreEvent(
                store_id="s", camera_id="c", visitor_id="v",
                event_type=EventType.ENTRY, timestamp=datetime.now(timezone.utc),
                confidence=0.9,
            )
            for _ in range(10)
        ]
        batch = EventBatch(events=events)
        assert len(batch.events) == 10

    def test_empty_batch(self):
        """An empty batch should be valid."""
        batch = EventBatch(events=[])
        assert len(batch.events) == 0

    # TODO: Add test for max batch size (500) when Pydantic enforces it

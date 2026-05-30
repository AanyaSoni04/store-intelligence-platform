"""
Pydantic v2 models for events and API responses.

All data flowing through the system is validated by these schemas.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# Event Types
# ════════════════════════════════════════════════════════════


class EventType(str, Enum):
    """All event types emitted by the detection pipeline."""

    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ZONE_ENTER = "ZONE_ENTER"
    ZONE_EXIT = "ZONE_EXIT"
    ZONE_DWELL = "ZONE_DWELL"
    BILLING_QUEUE_JOIN = "BILLING_QUEUE_JOIN"
    BILLING_QUEUE_ABANDON = "BILLING_QUEUE_ABANDON"
    REENTRY = "REENTRY"


# ════════════════════════════════════════════════════════════
# Core Event Model
# ════════════════════════════════════════════════════════════


class StoreEvent(BaseModel):
    """
    A single event emitted by the detection pipeline.

    The `metadata` dict carries event-type-specific fields:
        ENTRY:                {"bbox": [...], "gate_id": "...", "group_size": 1}
        EXIT:                 {"total_dwell_seconds": 487, "zones_visited": ["electronics"]}
        ZONE_ENTER:           {"zone_id": "electronics", "zone_name": "Electronics Aisle"}
        ZONE_EXIT:            {"zone_id": "electronics", "dwell_seconds": 124.5}
        ZONE_DWELL:           {"zone_id": "electronics", "dwell_seconds": 60, "is_prolonged": false}
        BILLING_QUEUE_JOIN:   {"queue_id": "checkout_1", "queue_position": 3}
        BILLING_QUEUE_ABANDON:{"queue_id": "checkout_1", "wait_seconds": 187.3}
        REENTRY:              {"original_visitor_id": "v_abc123", "gap_seconds": 120}
    """

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    store_id: str = Field(..., description="Store identifier")
    camera_id: str = Field(..., description="Camera that captured this event")
    visitor_id: str = Field(..., description="Unique visitor identifier")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="UTC timestamp of the event")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    metadata: dict = Field(default_factory=dict, description="Event-type-specific payload")

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# Batch Ingest
# ════════════════════════════════════════════════════════════


class EventBatch(BaseModel):
    """Batch of events for the ingest endpoint. Max 500 events per batch."""

    events: list[StoreEvent] = Field(..., max_length=500)


class IngestResponse(BaseModel):
    """Response from the batch ingest endpoint."""

    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    accepted: int
    rejected: int
    errors: list[str] = Field(default_factory=list)


# ════════════════════════════════════════════════════════════
# API Response Models
# ════════════════════════════════════════════════════════════


class MetricsResponse(BaseModel):
    """KPI snapshot for a store within a time window."""

    store_id: str
    window: str
    unique_visitors: int = 0
    conversion_rate: float = 0.0
    avg_dwell_seconds: float = 0.0
    queue_depth: int = 0
    abandonment_rate: float = 0.0
    computed_at: datetime


class FunnelStage(BaseModel):
    """A single stage in the visitor funnel."""

    stage: str
    count: int


class FunnelResponse(BaseModel):
    """Visitor funnel with drop-off rates between stages."""

    store_id: str
    window: str
    stages: list[FunnelStage]
    drop_off_rates: dict[str, float] = Field(default_factory=dict)


class ZoneHeat(BaseModel):
    """Visit frequency and dwell time for a single zone."""

    zone_id: str
    visit_count: int = 0
    avg_dwell_seconds: float = 0.0


class HeatmapResponse(BaseModel):
    """Zone-level heatmap data for a store."""

    store_id: str
    zones: list[ZoneHeat]


class Anomaly(BaseModel):
    """A detected anomaly."""

    anomaly_id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    severity: str = Field(..., description="low | medium | high")
    description: str
    detected_at: datetime
    visitor_id: str | None = None
    zone_id: str | None = None


class AnomalyResponse(BaseModel):
    """List of detected anomalies."""

    anomalies: list[Anomaly]


class HealthResponse(BaseModel):
    """System health check response."""

    status: str
    db: str
    uptime_seconds: float
    version: str
    event_count: int = 0

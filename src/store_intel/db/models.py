"""
SQLAlchemy ORM models — the 3-table schema.

Tables:
    stores   — registered retail stores
    visitors — deduplicated visitor identities
    events   — append-only event log (single source of truth)
"""

from sqlalchemy import Boolean, Column, Float, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Store(Base):
    """A registered retail store."""

    __tablename__ = "stores"

    store_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    timezone = Column(String, default="UTC")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    visitors = relationship("Visitor", back_populates="store")
    events = relationship("Event", back_populates="store")

    def __repr__(self) -> str:
        return f"<Store {self.store_id}: {self.name}>"


class Visitor(Base):
    """
    A deduplicated visitor identity.

    Each person detected by the pipeline gets a unique visitor_id.
    Staff members are flagged and excluded from KPI computations.
    """

    __tablename__ = "visitors"

    visitor_id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.store_id"), nullable=False, index=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_staff = Column(Boolean, default=False, nullable=False)
    merged_into = Column(String, ForeignKey("visitors.visitor_id"), nullable=True)
    visit_count = Column(Integer, default=1)

    # Relationships
    store = relationship("Store", back_populates="visitors")
    events = relationship("Event", back_populates="visitor")

    def __repr__(self) -> str:
        staff_tag = " [STAFF]" if self.is_staff else ""
        return f"<Visitor {self.visitor_id}{staff_tag}>"


class Event(Base):
    """
    Append-only event log.

    This is the single source of truth — all metrics, funnels, heatmaps,
    and anomalies are computed by querying this table.

    event_type values:
        ENTRY, EXIT, ZONE_ENTER, ZONE_EXIT, ZONE_DWELL,
        BILLING_QUEUE_JOIN, BILLING_QUEUE_ABANDON, REENTRY

    metadata_json stores event-specific payload as a JSON string:
        ENTRY:    {"bbox": [...], "gate_id": "...", "group_size": 1}
        ZONE_EXIT: {"zone_id": "...", "dwell_seconds": 124.5}
        etc.
    """

    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.store_id"), nullable=False, index=True)
    camera_id = Column(String, nullable=False, index=True)
    visitor_id = Column(String, ForeignKey("visitors.visitor_id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    metadata_json = Column(Text, default="{}")

    # Relationships
    store = relationship("Store", back_populates="events")
    visitor = relationship("Visitor", back_populates="events")

    def __repr__(self) -> str:
        return f"<Event {self.event_type} visitor={self.visitor_id} @ {self.timestamp}>"

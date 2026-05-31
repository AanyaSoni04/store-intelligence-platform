"""
CRUD helpers — reusable database query functions.

All database access goes through these helpers, keeping SQL out of
route handlers and analytics modules.
"""

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from store_intel.db.models import Event, Store, Visitor
from store_intel.events.schemas import StoreEvent, EventType

logger = logging.getLogger("store_intel")


# ── Stores ──────────────────────────────────────────────────


def get_store(db: Session, store_id: str) -> Store | None:
    """Fetch a store by ID, or None if not found."""
    return db.query(Store).filter(Store.store_id == store_id).first()


def get_or_create_store(db: Session, store_id: str, name: str = "") -> Store:
    """Get existing store or create a new one."""
    store = get_store(db, store_id)
    if store is None:
        store = Store(store_id=store_id, name=name or store_id)
        db.add(store)
        db.commit()
        db.refresh(store)
        logger.info("Created store", extra={"store_id": store_id})
    return store


# ── Visitors ────────────────────────────────────────────────


def get_visitor(db: Session, visitor_id: str) -> Visitor | None:
    """Fetch a visitor by ID."""
    return db.query(Visitor).filter(Visitor.visitor_id == visitor_id).first()


def get_or_create_visitor(db: Session, visitor_id: str, store_id: str) -> Visitor:
    """Get existing visitor or create a new one."""
    visitor = get_visitor(db, visitor_id)
    if visitor is None:
        visitor = Visitor(visitor_id=visitor_id, store_id=store_id)
        db.add(visitor)
        db.commit()
        db.refresh(visitor)
    return visitor


# ── Events ──────────────────────────────────────────────────


def insert_event(db: Session, event: StoreEvent) -> Event:
    """
    Insert a single event into the database.

    Automatically creates visitor record if it doesn't exist.
    """
    # Ensure visitor exists
    visitor = get_or_create_visitor(db, event.visitor_id, event.store_id)
    
    # 1. Forward existing merges
    while visitor.merged_into:
        event.visitor_id = visitor.merged_into
        visitor = get_or_create_visitor(db, event.visitor_id, event.store_id)

    # 2. Cross-camera session deduplication
    if event.event_type == EventType.ENTRY:
        # Check for recent exits globally across the store
        sixty_seconds_ago = event.timestamp - timedelta(seconds=60)
        recent_exit = db.query(Event).filter(
            Event.store_id == event.store_id,
            Event.event_type.in_([EventType.EXIT.value, EventType.ZONE_EXIT.value]),
            Event.timestamp >= sixty_seconds_ago,
            Event.timestamp <= event.timestamp
        ).order_by(Event.timestamp.desc()).first()
        
        if recent_exit and recent_exit.visitor_id != event.visitor_id:
            # We found a disconnected session. Merge incoming into previous.
            visitor.merged_into = recent_exit.visitor_id
            db.add(visitor)
            
            # Rewrite the event
            event.visitor_id = recent_exit.visitor_id
            event.event_type = EventType.REENTRY
            if event.metadata is None:
                event.metadata = {}
            event.metadata["cross_camera_merge"] = True
            
            # Update local reference
            visitor = get_or_create_visitor(db, event.visitor_id, event.store_id)
    
    # Update is_staff flag if staff events are detected
    if event.event_type in (EventType.STAFF_DETECTED, EventType.STAFF_EXCLUSION):
        visitor.is_staff = True
        db.add(visitor)

    db_event = Event(
        event_id=event.event_id,
        store_id=event.store_id,
        camera_id=event.camera_id,
        visitor_id=event.visitor_id,
        event_type=event.event_type.value,
        timestamp=event.timestamp,
        confidence=event.confidence,
        metadata_json=json.dumps(event.metadata),
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def insert_events_batch(db: Session, events: list[StoreEvent]) -> tuple[int, int, list[str]]:
    """
    Insert a batch of events. Returns (accepted_count, rejected_count, error_messages).

    Each event is inserted independently — a single bad event doesn't block the batch.
    """
    accepted = 0
    rejected = 0
    errors: list[str] = []

    for event in events:
        try:
            insert_event(db, event)
            accepted += 1
        except Exception as e:
            rejected += 1
            errors.append(f"Event {event.event_id}: {str(e)}")
            db.rollback()
            logger.warning(
                "Failed to insert event",
                extra={"event_id": event.event_id, "error": str(e)},
            )

    return accepted, rejected, errors


def query_events(
    db: Session,
    store_id: str,
    event_type: str | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    exclude_staff: bool = True,
) -> list[Event]:
    """
    Query events with optional filters.

    TODO: Add pagination for large result sets.
    TODO: Optimize with proper SQL indexes once query patterns stabilize.
    """
    query = db.query(Event).filter(Event.store_id == store_id)

    if event_type:
        query = query.filter(Event.event_type == event_type)

    if from_time:
        query = query.filter(Event.timestamp >= from_time)

    if to_time:
        query = query.filter(Event.timestamp <= to_time)

    if exclude_staff:
        # Join with visitors to filter out staff
        query = query.join(Visitor).filter(Visitor.is_staff == False)  # noqa: E712

    return query.order_by(Event.timestamp.asc()).all()

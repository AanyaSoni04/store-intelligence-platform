"""
POST /events/ingest — Batch event ingestion endpoint.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from store_intel.db.engine import get_db
from store_intel.db.crud import get_or_create_store, insert_events_batch
from store_intel.events.schemas import EventBatch, IngestResponse

logger = logging.getLogger("store_intel")
router = APIRouter(tags=["Events"])


@router.post("/events/ingest", response_model=IngestResponse, status_code=202)
def ingest_events(batch: EventBatch, db: Session = Depends(get_db)) -> IngestResponse:
    """
    Ingest a batch of detection events.

    Validates each event independently — a single bad event does not block the batch.
    Automatically creates store and visitor records as needed.
    """
    # Ensure all referenced stores exist
    store_ids = {e.store_id for e in batch.events}
    for sid in store_ids:
        get_or_create_store(db, sid)

    accepted, rejected, errors = insert_events_batch(db, batch.events)

    logger.info(
        "Batch ingested",
        extra={"accepted": accepted, "rejected": rejected, "total": len(batch.events)},
    )

    # TODO: Push accepted events to WebSocket for live dashboard updates

    return IngestResponse(accepted=accepted, rejected=rejected, errors=errors)

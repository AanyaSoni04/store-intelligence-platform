import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from store_intel.db.engine import get_db
from store_intel.db.crud import get_or_create_store, insert_events_batch
from store_intel.events.schemas import EventBatch, IngestResponse
from store_intel.api.websocket import manager 

logger = logging.getLogger("store_intel")
router = APIRouter(tags=["Events"])

@router.post("/events/ingest", response_model=IngestResponse, status_code=202)
async def ingest_events(batch: EventBatch, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> IngestResponse:
    store_ids = {e.store_id for e in batch.events}
    for sid in store_ids:
        get_or_create_store(db, sid)
    accepted, rejected, errors = insert_events_batch(db, batch.events)
    logger.info("Batch ingested", extra={"accepted": accepted, "rejected": rejected})
    if accepted > 0:
        background_tasks.add_task(manager.broadcast, {"type": "EVENTS_INGESTED", "count": accepted, "stores": list(store_ids)})
    return IngestResponse(accepted=accepted, rejected=rejected, errors=errors)
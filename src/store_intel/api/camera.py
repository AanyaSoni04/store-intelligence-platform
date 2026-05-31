from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
from store_intel.db.engine import get_db

router = APIRouter(tags=["Camera Dashboard"])

@router.get("/camera/live/{camera_id}")
def get_camera_live(camera_id: str, db: Session = Depends(get_db)):
    """
    Returns live operational statistics for a specific camera computed from real database events.
    """
    now = datetime.now(timezone.utc)
    # Define "today" as the last 24 hours to ensure we capture events regardless of timezone offset
    from_time = now - timedelta(days=1)

    # current_visitors: Unique visitors seen by this camera in the last 15 minutes
    q_current = text("""
        SELECT COUNT(DISTINCT visitor_id) 
        FROM events 
        WHERE camera_id = :camera_id 
          AND timestamp >= :current_from_time
    """)
    current_from_time = now - timedelta(minutes=15)
    current_visitors = db.execute(q_current, {"camera_id": camera_id, "current_from_time": current_from_time}).scalar() or 0

    # entered_today: ZONE_ENTER (or ENTRY) for this camera today
    q_entered = text("""
        SELECT COUNT(*)
        FROM events
        WHERE camera_id = :camera_id
          AND event_type IN ('ZONE_ENTER', 'ENTRY')
          AND timestamp >= :from_time
    """)
    entered_today = db.execute(q_entered, {"camera_id": camera_id, "from_time": from_time}).scalar() or 0

    # exited_today: ZONE_EXIT (or EXIT) for this camera today
    q_exited = text("""
        SELECT COUNT(*)
        FROM events
        WHERE camera_id = :camera_id
          AND event_type IN ('ZONE_EXIT', 'EXIT')
          AND timestamp >= :from_time
    """)
    exited_today = db.execute(q_exited, {"camera_id": camera_id, "from_time": from_time}).scalar() or 0

    # billing_queue: Events relating to the billing queue
    q_billing = text("""
        SELECT COUNT(*)
        FROM events
        WHERE camera_id = :camera_id
          AND (event_type = 'BILLING_QUEUE_JOIN' OR json_extract(metadata_json, '$.zone_id') = 'billing_queue')
          AND timestamp >= :from_time
    """)
    billing_queue = db.execute(q_billing, {"camera_id": camera_id, "from_time": from_time}).scalar() or 0

    # checkout_counter: Events relating to the checkout counter
    q_checkout = text("""
        SELECT COUNT(*)
        FROM events
        WHERE camera_id = :camera_id
          AND json_extract(metadata_json, '$.zone_id') = 'checkout_counter'
          AND timestamp >= :from_time
    """)
    checkout_counter = db.execute(q_checkout, {"camera_id": camera_id, "from_time": from_time}).scalar() or 0

    return {
        "current_visitors": current_visitors,
        "entered_today": entered_today,
        "exited_today": exited_today,
        "billing_queue": billing_queue,
        "checkout_counter": checkout_counter
    }

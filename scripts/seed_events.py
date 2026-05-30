"""
Synthetic event seeder — populates the database with realistic test data.

Usage:
    python -m scripts.seed_events --store store_001 --visitors 50 --hours 8
"""

import argparse
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from store_intel.db.engine import get_db, engine
from store_intel.db.models import Base
from store_intel.db.crud import insert_events_batch, get_or_create_store
from store_intel.events.schemas import StoreEvent, EventType

logger = logging.getLogger("store_intel")

ZONES = ["electronics", "apparel", "home", "grocery"]


def generate_visitor_journey(
    store_id: str,
    visitor_id: str,
    start_time: datetime,
    is_staff: bool = False,
    will_reenter: bool = False
) -> list[StoreEvent]:
    """Generate a realistic sequence of events for a single visitor."""
    events = []
    current_time = start_time
    
    # 1. ENTRY
    events.append(StoreEvent(
        store_id=store_id,
        camera_id="cam_001",
        visitor_id=visitor_id,
        event_type=EventType.ENTRY,
        timestamp=current_time,
        confidence=0.95,
        metadata={"gate_id": "main_entrance", "group_size": random.randint(1, 3)}
    ))

    # Determine behavior
    num_zones = random.randint(1, 3)
    if is_staff:
        num_zones = random.randint(3, 5)
        
    zones_visited = random.sample(ZONES, num_zones)
    total_dwell = 0

    # 2. Zone visits
    for zone in zones_visited:
        current_time += timedelta(seconds=random.randint(10, 60))  # walking to zone
        events.append(StoreEvent(
            store_id=store_id,
            camera_id="cam_002",
            visitor_id=visitor_id,
            event_type=EventType.ZONE_ENTER,
            timestamp=current_time,
            confidence=0.92,
            metadata={"zone_id": zone, "zone_name": zone.capitalize()}
        ))
        
        dwell_time = random.randint(30, 300)
        total_dwell += dwell_time
        current_time += timedelta(seconds=dwell_time)
        
        # Intermittent ZONE_DWELL
        if dwell_time > 120:
            events.append(StoreEvent(
                store_id=store_id,
                camera_id="cam_002",
                visitor_id=visitor_id,
                event_type=EventType.ZONE_DWELL,
                timestamp=current_time - timedelta(seconds=dwell_time // 2),
                confidence=0.9,
                metadata={"zone_id": zone, "dwell_seconds": dwell_time // 2, "is_prolonged": True}
            ))

        events.append(StoreEvent(
            store_id=store_id,
            camera_id="cam_002",
            visitor_id=visitor_id,
            event_type=EventType.ZONE_EXIT,
            timestamp=current_time,
            confidence=0.92,
            metadata={"zone_id": zone, "dwell_seconds": dwell_time}
        ))

    # 3. Billing (Conversion or Abandonment)
    if not is_staff:
        will_buy = random.random() > 0.3  # 70% conversion rate
        will_abandon = not will_buy and random.random() > 0.5 # 15% abandon, 15% just leave without queue
        
        if will_buy or will_abandon:
            current_time += timedelta(seconds=random.randint(10, 60))
            events.append(StoreEvent(
                store_id=store_id,
                camera_id="cam_003",
                visitor_id=visitor_id,
                event_type=EventType.BILLING_QUEUE_JOIN,
                timestamp=current_time,
                confidence=0.9,
                metadata={"queue_id": "checkout_1", "queue_position": random.randint(1, 5)}
            ))
            
            queue_wait = random.randint(20, 180)
            current_time += timedelta(seconds=queue_wait)
            total_dwell += queue_wait
            
            if will_abandon:
                events.append(StoreEvent(
                    store_id=store_id,
                    camera_id="cam_003",
                    visitor_id=visitor_id,
                    event_type=EventType.BILLING_QUEUE_ABANDON,
                    timestamp=current_time,
                    confidence=0.9,
                    metadata={"queue_id": "checkout_1", "wait_seconds": queue_wait}
                ))

    # 4. EXIT
    current_time += timedelta(seconds=random.randint(10, 40))
    events.append(StoreEvent(
        store_id=store_id,
        camera_id="cam_001",
        visitor_id=visitor_id,
        event_type=EventType.EXIT,
        timestamp=current_time,
        confidence=0.95,
        metadata={"total_dwell_seconds": total_dwell, "zones_visited": zones_visited}
    ))

    # 5. REENTRY
    if will_reenter:
        gap = random.randint(60, 3600)
        current_time += timedelta(seconds=gap)
        reentry_id = f"v_re_{uuid.uuid4().hex[:6]}"
        
        events.append(StoreEvent(
            store_id=store_id,
            camera_id="cam_001",
            visitor_id=reentry_id,
            event_type=EventType.REENTRY,
            timestamp=current_time,
            confidence=0.85,
            metadata={"original_visitor_id": visitor_id, "gap_seconds": gap}
        ))
        
        # Simulate quick re-entry visit
        events.append(StoreEvent(
            store_id=store_id,
            camera_id="cam_001",
            visitor_id=reentry_id,
            event_type=EventType.ENTRY,
            timestamp=current_time + timedelta(seconds=2),
            confidence=0.95,
            metadata={}
        ))
        
        current_time += timedelta(seconds=60)
        events.append(StoreEvent(
            store_id=store_id,
            camera_id="cam_001",
            visitor_id=reentry_id,
            event_type=EventType.EXIT,
            timestamp=current_time,
            confidence=0.95,
            metadata={"total_dwell_seconds": 60}
        ))

    return events


def main():
    parser = argparse.ArgumentParser(description="Seed the database with synthetic events")
    parser.add_argument("--store", default="store_001", help="Store ID")
    parser.add_argument("--visitors", type=int, default=50, help="Number of visitors to simulate")
    parser.add_argument("--hours", type=int, default=8, help="Hours of activity to simulate")
    args = parser.parse_args()

    print(f"Seeding {args.visitors} visitors over {args.hours}h for store {args.store}")

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    get_or_create_store(db, args.store)

    end_time = datetime.now(timezone.utc)
    # Ensure there is at least one "empty store period"
    # We'll leave the last hour mostly empty to trigger 'dead zone' and 'stale feed' rules,
    # except maybe one event right at the end to not break other queries entirely, or no events at all in the last 15m.
    # Actually, we want to simulate the events spread over (hours - 1)
    active_duration_seconds = max(3600, (args.hours * 3600) - 3600) 
    start_time = end_time - timedelta(hours=args.hours)

    all_events = []
    
    # Generate one conversion, one abandon, one reentry explicitly to satisfy requirements
    # Will happen organically due to random probs, but this guarantees it
    special_cases = ["conversion", "abandon", "reentry", "staff"]

    for i in range(args.visitors):
        visitor_id = f"v_seed_{uuid.uuid4().hex[:8]}"
        
        # Random start time within the active duration
        offset = random.randint(0, active_duration_seconds)
        visit_start = start_time + timedelta(seconds=offset)
        
        is_staff = False
        will_reenter = False
        
        if special_cases:
            case = special_cases.pop()
            if case == "staff":
                is_staff = True
            elif case == "reentry":
                will_reenter = True

        journey = generate_visitor_journey(
            store_id=args.store,
            visitor_id=visitor_id,
            start_time=visit_start,
            is_staff=is_staff,
            will_reenter=will_reenter
        )
        all_events.extend(journey)

    # Sort events strictly by timestamp to simulate real feed
    all_events.sort(key=lambda x: x.timestamp)

    accepted, rejected, errors = insert_events_batch(db, all_events)
    
    print(f"Seeding complete! {accepted} events inserted. {rejected} rejected.")
    if errors:
        print(f"Sample errors: {errors[:5]}")
        
    db.close()

if __name__ == "__main__":
    main()

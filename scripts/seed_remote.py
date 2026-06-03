import random
import uuid
import requests
from datetime import datetime, timedelta, timezone

ZONES = ["entrance zone", "checkout counter", "billing queue"]

def generate_visitor_journey(store_id: str, visitor_id: str, start_time: datetime, is_staff: bool = False, will_reenter: bool = False):
    events = []
    current_time = start_time
    
    events.append({
        "store_id": store_id,
        "camera_id": "cam_001",
        "visitor_id": visitor_id,
        "event_type": "ENTRY",
        "timestamp": current_time.isoformat(),
        "confidence": 0.95,
        "metadata": {"gate_id": "main_entrance", "group_size": random.randint(1, 3)}
    })

    num_zones = random.randint(1, 3)
    if is_staff:
        num_zones = random.randint(3, 5)
        
    num_zones = min(num_zones, len(ZONES))
    zones_visited = random.sample(ZONES, num_zones)
    total_dwell = 0

    for zone in zones_visited:
        current_time += timedelta(seconds=random.randint(10, 60))
        events.append({
            "store_id": store_id,
            "camera_id": "cam_002",
            "visitor_id": visitor_id,
            "event_type": "ZONE_ENTER",
            "timestamp": current_time.isoformat(),
            "confidence": 0.92,
            "metadata": {"zone_id": zone, "zone_name": zone.capitalize()}
        })
        
        dwell_time = random.randint(30, 300)
        total_dwell += dwell_time
        current_time += timedelta(seconds=dwell_time)
        
        if dwell_time > 120:
            events.append({
                "store_id": store_id,
                "camera_id": "cam_002",
                "visitor_id": visitor_id,
                "event_type": "ZONE_DWELL",
                "timestamp": (current_time - timedelta(seconds=dwell_time // 2)).isoformat(),
                "confidence": 0.9,
                "metadata": {"zone_id": zone, "dwell_seconds": dwell_time // 2, "is_prolonged": True}
            })

        events.append({
            "store_id": store_id,
            "camera_id": "cam_002",
            "visitor_id": visitor_id,
            "event_type": "ZONE_EXIT",
            "timestamp": current_time.isoformat(),
            "confidence": 0.92,
            "metadata": {"zone_id": zone, "dwell_seconds": dwell_time}
        })

    if not is_staff:
        will_buy = random.random() > 0.3
        will_abandon = not will_buy and random.random() > 0.5
        
        if will_buy or will_abandon:
            current_time += timedelta(seconds=random.randint(10, 60))
            events.append({
                "store_id": store_id,
                "camera_id": "cam_003",
                "visitor_id": visitor_id,
                "event_type": "BILLING_QUEUE_JOIN",
                "timestamp": current_time.isoformat(),
                "confidence": 0.9,
                "metadata": {"queue_id": "checkout_1", "queue_position": random.randint(1, 5)}
            })
            
            queue_wait = random.randint(20, 180)
            current_time += timedelta(seconds=queue_wait)
            total_dwell += queue_wait
            
            if will_abandon:
                events.append({
                    "store_id": store_id,
                    "camera_id": "cam_003",
                    "visitor_id": visitor_id,
                    "event_type": "BILLING_QUEUE_ABANDON",
                    "timestamp": current_time.isoformat(),
                    "confidence": 0.9,
                    "metadata": {"queue_id": "checkout_1", "wait_seconds": queue_wait}
                })
            else:
                events.append({
                    "store_id": store_id,
                    "camera_id": "cam_003",
                    "visitor_id": visitor_id,
                    "event_type": "PURCHASE_PROXY",
                    "timestamp": current_time.isoformat(),
                    "confidence": 0.95,
                    "metadata": {"queue_id": "checkout_1", "wait_seconds": queue_wait, "transaction_value": round(random.uniform(10.0, 150.0), 2)}
                })

    current_time += timedelta(seconds=random.randint(10, 40))
    events.append({
        "store_id": store_id,
        "camera_id": "cam_001",
        "visitor_id": visitor_id,
        "event_type": "EXIT",
        "timestamp": current_time.isoformat(),
        "confidence": 0.95,
        "metadata": {"total_dwell_seconds": total_dwell, "zones_visited": zones_visited}
    })

    return events

def main():
    store_id = "my_store"
    visitors = 200
    hours = 24
    url = "https://store-intelligence-api-76n7.onrender.com/events/ingest"

    print(f"Seeding {visitors} visitors over {hours}h for {store_id} to {url}")
    
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    all_events = []
    special_cases = ["conversion", "abandon", "reentry", "staff"]
    
    for i in range(visitors):
        visitor_id = f"v_seed_{uuid.uuid4().hex[:8]}"
        offset = random.randint(0, hours * 3600)
        visit_start = start_time + timedelta(seconds=offset)
        
        is_staff = False
        will_reenter = False
        if special_cases:
            case = special_cases.pop()
            if case == "staff": is_staff = True
            elif case == "reentry": will_reenter = True
            
        journey = generate_visitor_journey(store_id, visitor_id, visit_start, is_staff, will_reenter)
        all_events.extend(journey)
        
    all_events.sort(key=lambda x: x["timestamp"])
    
    print(f"Generated {len(all_events)} events. Sending to API in chunks...")
    
    chunk_size = 500
    for i in range(0, len(all_events), chunk_size):
        chunk = all_events[i:i+chunk_size]
        try:
            resp = requests.post(url, json={"events": chunk})
            print(f"Chunk {i//chunk_size + 1}: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Failed chunk {i//chunk_size + 1}: {e}")

if __name__ == '__main__':
    main()

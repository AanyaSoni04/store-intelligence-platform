import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from store_intel.db.engine import SessionLocal

def test():
    db = SessionLocal()
    from_time = datetime.now(timezone.utc) - timedelta(days=2) # sufficiently large
    
    q1 = text("""
        SELECT COUNT(DISTINCT e.visitor_id) 
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type = 'ENTRY' 
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
    """)
    unique_visitors = db.execute(q1, {"store_id": "test_store", "from_time": from_time}).scalar() or 0
    print("Unique visitors:", unique_visitors)

    q2 = text("""
        SELECT COUNT(DISTINCT e.visitor_id) 
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type = 'PURCHASE_PROXY' 
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
    """)
    purchases = db.execute(q2, {"store_id": "test_store", "from_time": from_time}).scalar() or 0
    print("Purchases:", purchases)
    
    q3 = text("""
        SELECT AVG(json_extract(e.metadata_json, '$.total_dwell_seconds')) 
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = :store_id 
          AND e.event_type = 'EXIT' 
          AND e.timestamp >= :from_time
          AND v.is_staff = 0
    """)
    avg_dwell = db.execute(q3, {"store_id": "test_store", "from_time": from_time}).scalar() or 0.0
    print("Avg Dwell:", avg_dwell)

if __name__ == "__main__":
    test()

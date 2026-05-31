import pytest
from store_intel.tracking.staff import StaffDetector
from store_intel.db.models import Visitor

def test_staff_detector(db_session, sample_store):
    detector = StaffDetector()
    
    # Create visitor
    v = Visitor(visitor_id="v1", store_id=sample_store.store_id, is_staff=False)
    db_session.add(v)
    db_session.commit()
    
    assert detector.is_staff("v1", db_session) == False
    detector.mark_as_staff("v1", db_session)
    assert detector.is_staff("v1", db_session) == True
    
    assert detector.check_behavioral("v1", 4000, db_session) == False

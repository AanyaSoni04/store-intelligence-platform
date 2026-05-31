from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from store_intel.db.engine import get_db
from store_intel.tracking.staff import StaffDetector
from store_intel.db.models import Visitor

router = APIRouter(prefix="/stores/{store_id}/visitors", tags=["Staff"])

@router.post("/{visitor_id}/staff", status_code=status.HTTP_200_OK)
def mark_as_staff(store_id: str, visitor_id: str, db: Session = Depends(get_db)):
    """Manually mark a visitor as store staff to exclude them from metrics."""
    # Check if visitor exists
    visitor = db.query(Visitor).filter(Visitor.store_id == store_id, Visitor.visitor_id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
        
    StaffDetector.mark_as_staff(visitor_id, db)
    return {"message": f"Visitor {visitor_id} marked as staff", "visitor_id": visitor_id, "is_staff": True}

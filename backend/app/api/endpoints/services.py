from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.trace_service import TraceService

router = APIRouter()
trace_service = TraceService()


@router.get("/map")
def get_service_map(db: Session = Depends(get_db)):
    return trace_service.get_service_map(db)


@router.get("/metrics")
def get_service_metrics(db: Session = Depends(get_db)):
    return trace_service.get_service_metrics(db)

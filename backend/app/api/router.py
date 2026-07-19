from fastapi import APIRouter
from app.api.endpoints import spans, traces, services, websocket

api_router = APIRouter()

api_router.include_router(spans.router, prefix="/spans", tags=["spans"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(websocket.router, tags=["websocket"])

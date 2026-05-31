"""
Lightweight endpoint for receiving live telemetry from the pipeline and broadcasting it via WebSockets.
"""

from fastapi import APIRouter
from store_intel.api.websocket import manager

router = APIRouter(tags=["Telemetry"])

@router.post("/telemetry")
async def receive_telemetry(payload: dict):
    """
    Receive live telemetry from DetectionPipeline and instantly broadcast to all connected WebSocket clients.
    """
    await manager.broadcast({
        "type": "LIVE_TELEMETRY",
        "data": payload
    })
    return {"status": "broadcasted"}

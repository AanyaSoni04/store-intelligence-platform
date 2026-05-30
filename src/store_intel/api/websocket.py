"""
WebSocket endpoint for live dashboard updates.

TODO: Implement:
    - WebSocket connection manager (track connected clients)
    - Broadcast new events to all connected clients
    - Broadcast metric updates on a configurable interval
    - Handle client disconnection gracefully
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("store_intel")
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages active WebSocket connections.

    TODO: Implement:
        - connect(websocket): accept and track a new client
        - disconnect(websocket): remove a client
        - broadcast(message): send JSON to all connected clients
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected", extra={"total": len(self.active_connections)})

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected", extra={"total": len(self.active_connections)})

    async def broadcast(self, message: dict) -> None:
        """Send a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # TODO: Handle stale connections
                pass


# Singleton manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time dashboard updates.

    TODO: Implement:
        - Send initial state snapshot on connect
        - Listen for client filter preferences
        - Push event/metric updates via manager.broadcast()
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; listen for client messages
            data = await websocket.receive_text()
            # TODO: Handle client filter messages (e.g., subscribe to specific store)
            logger.debug("WebSocket received", extra={"data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

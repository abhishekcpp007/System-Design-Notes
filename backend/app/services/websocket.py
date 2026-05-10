"""
WebSocket Connection Manager.

Provides:
- Connection lifecycle management (connect/disconnect/heartbeat)
- Room-based broadcasting (analytics, notifications)
- Authentication via token in query params
- Automatic reconnection support
- Message serialization/deserialization
"""
import asyncio
import json
import time
from typing import Optional
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect, Query, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.utils.security import decode_access_token

settings = get_settings()
router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections with room-based broadcasting.

    Rooms:
    - "analytics": Live analytics dashboard feed
    - "notifications:{user_id}": Per-user notifications
    - "admin": Admin-only broadcast channel
    """

    def __init__(self):
        # room_name -> set of WebSocket connections
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.connection_metadata: dict[WebSocket, dict] = {}
        self._heartbeat_interval = 30  # seconds

    async def connect(
        self, websocket: WebSocket, room: str, user_id: Optional[int] = None
    ):
        """Accept connection and add to room."""
        await websocket.accept()

        if room not in self.active_connections:
            self.active_connections[room] = set()
        self.active_connections[room].add(websocket)

        self.connection_metadata[websocket] = {
            "room": room,
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_heartbeat": time.time(),
        }

    def disconnect(self, websocket: WebSocket):
        """Remove connection from all rooms."""
        metadata = self.connection_metadata.pop(websocket, None)
        if metadata:
            room = metadata["room"]
            if room in self.active_connections:
                self.active_connections[room].discard(websocket)
                if not self.active_connections[room]:
                    del self.active_connections[room]

    async def broadcast(self, room: str, message: dict):
        """Send message to all connections in a room."""
        if room not in self.active_connections:
            return

        dead_connections = set()
        for connection in self.active_connections[room]:
            try:
                await connection.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                dead_connections.add(connection)

        # Cleanup dead connections
        for conn in dead_connections:
            self.disconnect(conn)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to a specific user's notification channel."""
        room = f"notifications:{user_id}"
        await self.broadcast(room, message)

    async def broadcast_analytics_event(self, event_data: dict):
        """Broadcast a real-time analytics event to the analytics room."""
        await self.broadcast("analytics", {
            "type": "analytics_event",
            "data": event_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_connection_count(self, room: Optional[str] = None) -> int:
        """Get number of active connections, optionally filtered by room."""
        if room:
            return len(self.active_connections.get(room, set()))
        return sum(len(conns) for conns in self.active_connections.values())

    def get_room_stats(self) -> dict:
        """Get stats about all active rooms."""
        return {
            room: len(connections)
            for room, connections in self.active_connections.items()
        }


# Singleton connection manager
manager = ConnectionManager()


# ============================================================
# WebSocket Endpoints
# ============================================================


@router.websocket("/ws/analytics")
async def analytics_websocket(websocket: WebSocket, token: str = Query(default="")):
    """
    Real-time analytics feed.

    Requires admin token in query params.
    Broadcasts: page views, active visitors, live events.
    """
    # Authenticate
    user_data = decode_access_token(token) if token else None
    if not user_data or user_data.get("role") != "admin":
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket, "analytics", user_id=user_data.get("user_id"))

    # Send initial state
    await websocket.send_json({
        "type": "connected",
        "room": "analytics",
        "active_connections": manager.get_connection_count(),
    })

    try:
        while True:
            # Wait for messages (heartbeat/commands)
            data = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=manager._heartbeat_interval + 5,
            )

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})
                meta = manager.connection_metadata.get(websocket)
                if meta:
                    meta["last_heartbeat"] = time.time()

    except (WebSocketDisconnect, asyncio.TimeoutError, RuntimeError):
        manager.disconnect(websocket)


@router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket, token: str = Query(default="")):
    """
    Per-user notification channel.

    Sends: new contact messages (admin), system alerts, background job completions.
    """
    user_data = decode_access_token(token) if token else None
    if not user_data:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user_id = user_data.get("user_id")
    room = f"notifications:{user_id}"

    await manager.connect(websocket, room, user_id=user_id)

    await websocket.send_json({
        "type": "connected",
        "room": "notifications",
        "user_id": user_id,
    })

    try:
        while True:
            data = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=manager._heartbeat_interval + 5,
            )

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})

    except (WebSocketDisconnect, asyncio.TimeoutError, RuntimeError):
        manager.disconnect(websocket)


@router.get("/ws/stats", tags=["WebSocket"])
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": manager.get_connection_count(),
        "rooms": manager.get_room_stats(),
    }

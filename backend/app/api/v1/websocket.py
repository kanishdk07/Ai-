"""
WebSocket API Route
Handles real-time dashboard connections
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.services.websocket_service import get_connection_manager
from app.utils.security import decode_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
):
    """
    WebSocket endpoint for real-time dashboard updates

    Query Parameters:
    - token: JWT access token

    Events broadcasted:
    - incident_created: New accident detected
    - incident_updated: Incident status or details changed
    - incident_acknowledged: Hospital acknowledged incident
    - incident_resolved: Incident resolved or closed
    - notification_sent: Emergency notification sent
    - notifications_stopped: Notifications stopped for incident
    - camera_status_changed: Camera status changed
    - maintenance_mode_changed: System maintenance mode toggled
    - system_alert: System-wide alerts

    Message format:
    {
        "type": "event_type",
        "data": {...},
        "timestamp": "ISO8601 timestamp"
    }
    """
    manager = get_connection_manager()

    # Verify token
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Accept connection
    await manager.connect(websocket, user_id)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "Connected to dashboard WebSocket",
                "user_id": user_id,
            },
            "timestamp": None,
        })

        # Keep connection alive and handle incoming messages
        while True:
            # Receive messages (for heartbeat or client actions)
            data = await websocket.receive_text()

            # Handle heartbeat
            if data == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "data": {},
                    "timestamp": None,
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected: user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(websocket, user_id)

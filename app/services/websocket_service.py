"""
WebSocket Service
Handles real-time WebSocket connections and broadcasts
"""

from typing import Dict, Set, List
from uuid import UUID
from fastapi import WebSocket
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: user {user_id}, total connections: {self.get_connection_count()}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Remove user entry if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(f"WebSocket disconnected: user {user_id}, remaining connections: {self.get_connection_count()}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to a specific user's connections"""
        if user_id in self.active_connections:
            disconnected = set()

            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")
                    disconnected.add(websocket)

            # Clean up disconnected sockets
            for websocket in disconnected:
                self.active_connections[user_id].discard(websocket)

    async def broadcast(self, message: dict, exclude_user: str = None):
        """Broadcast message to all connected clients"""
        disconnected = []

        for user_id, connections in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                    disconnected.append((user_id, websocket))

        # Clean up disconnected sockets
        for user_id, websocket in disconnected:
            self.disconnect(websocket, user_id)

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_user_count(self) -> int:
        """Get number of connected users"""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


class WebSocketService:
    """Service for WebSocket event broadcasting"""

    @staticmethod
    async def broadcast_incident_created(incident_data: dict):
        """Broadcast new incident detection"""
        message = {
            "type": "incident_created",
            "data": incident_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted incident_created: {incident_data.get('incident_id')}")

    @staticmethod
    async def broadcast_incident_updated(incident_data: dict):
        """Broadcast incident update"""
        message = {
            "type": "incident_updated",
            "data": incident_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted incident_updated: {incident_data.get('incident_id')}")

    @staticmethod
    async def broadcast_notification_sent(notification_data: dict):
        """Broadcast notification sent event"""
        message = {
            "type": "notification_sent",
            "data": notification_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted notification_sent: {notification_data.get('notification_id')}")

    @staticmethod
    async def broadcast_incident_acknowledged(incident_data: dict):
        """Broadcast incident acknowledgment"""
        message = {
            "type": "incident_acknowledged",
            "data": incident_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted incident_acknowledged: {incident_data.get('incident_id')}")

    @staticmethod
    async def broadcast_incident_resolved(incident_data: dict):
        """Broadcast incident resolution"""
        message = {
            "type": "incident_resolved",
            "data": incident_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted incident_resolved: {incident_data.get('incident_id')}")

    @staticmethod
    async def broadcast_notifications_stopped(incident_id: str, reason: str = None):
        """Broadcast notification stop event"""
        message = {
            "type": "notifications_stopped",
            "data": {
                "incident_id": incident_id,
                "reason": reason,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted notifications_stopped: {incident_id}")

    @staticmethod
    async def broadcast_camera_status_changed(camera_data: dict):
        """Broadcast camera status change"""
        message = {
            "type": "camera_status_changed",
            "data": camera_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted camera_status_changed: {camera_data.get('camera_id')}")

    @staticmethod
    async def broadcast_maintenance_mode_changed(enabled: bool, reason: str = None):
        """Broadcast maintenance mode change"""
        message = {
            "type": "maintenance_mode_changed",
            "data": {
                "enabled": enabled,
                "reason": reason,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted maintenance_mode_changed: {enabled}")

    @staticmethod
    async def broadcast_system_alert(alert_type: str, message_text: str):
        """Broadcast system alert"""
        message = {
            "type": "system_alert",
            "data": {
                "alert_type": alert_type,
                "message": message_text,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)
        logger.debug(f"Broadcasted system_alert: {alert_type}")


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return manager

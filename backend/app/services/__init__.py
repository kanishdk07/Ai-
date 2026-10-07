"""
Services Package
Exports all service classes
"""

from app.services.auth_service import AuthService
from app.services.camera_service import CameraService
from app.services.incident_service import IncidentService
from app.services.hospital_service import HospitalService
from app.services.notification_service import NotificationService
from app.services.scheduler_service import SchedulerService, get_scheduler
from app.services.websocket_service import WebSocketService, ConnectionManager, get_connection_manager

__all__ = [
    "AuthService",
    "CameraService",
    "IncidentService",
    "HospitalService",
    "NotificationService",
    "SchedulerService",
    "get_scheduler",
    "WebSocketService",
    "ConnectionManager",
    "get_connection_manager",
]

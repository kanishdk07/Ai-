"""
Schemas Package
Exports all Pydantic schemas
"""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    TokenData,
    LoginRequest,
    RefreshTokenRequest,
)
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraActionRequest,
)
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentListResponse,
    IncidentAcknowledgeRequest,
    IncidentAcknowledgeResponse,
    IncidentResolveRequest,
    IncidentCancelRequest,
)
from app.schemas.hospital import (
    HospitalCreate,
    HospitalUpdate,
    HospitalResponse,
    HospitalListResponse,
    NearbyHospitalResponse,
    NearbyHospitalsRequest,
)
from app.schemas.notification import (
    ManualNotificationRequest,
    NotificationResponse,
    NotificationListResponse,
    StopNotificationRequest,
)
from app.schemas.admin import (
    SystemSettingsUpdate,
    SystemSettingsResponse,
    MaintenanceModeRequest,
    MaintenanceModeResponse,
    SystemHealthResponse,
    AuditLogResponse,
    AuditLogListResponse,
    EmergencyStopRequest,
    EmergencyStopResponse,
)

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "Token",
    "TokenData",
    "LoginRequest",
    "RefreshTokenRequest",
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "CameraListResponse",
    "CameraActionRequest",
    "IncidentCreate",
    "IncidentUpdate",
    "IncidentResponse",
    "IncidentListResponse",
    "IncidentAcknowledgeRequest",
    "IncidentAcknowledgeResponse",
    "IncidentResolveRequest",
    "IncidentCancelRequest",
    "HospitalCreate",
    "HospitalUpdate",
    "HospitalResponse",
    "HospitalListResponse",
    "NearbyHospitalResponse",
    "NearbyHospitalsRequest",
    "ManualNotificationRequest",
    "NotificationResponse",
    "NotificationListResponse",
    "StopNotificationRequest",
    "SystemSettingsUpdate",
    "SystemSettingsResponse",
    "MaintenanceModeRequest",
    "MaintenanceModeResponse",
    "SystemHealthResponse",
    "AuditLogResponse",
    "AuditLogListResponse",
    "EmergencyStopRequest",
    "EmergencyStopResponse",
]

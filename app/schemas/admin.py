"""
Admin Schemas
Pydantic models for admin-related requests and responses
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class SystemSettingsUpdate(BaseModel):
    """Schema for updating system settings"""
    auto_notification_enabled: Optional[bool] = Field(None, description="Enable/disable automatic notifications")
    notification_interval_seconds: Optional[int] = Field(None, ge=30, le=300, description="Repeat interval (30-300 seconds)")
    hospital_search_radius_km: Optional[float] = Field(None, gt=0, le=200)
    max_hospitals_to_notify: Optional[int] = Field(None, ge=1, le=20)
    max_notification_retries: Optional[int] = Field(None, ge=1, le=50)
    test_mode: Optional[bool] = Field(None, description="Enable/disable test mode")


class SystemSettingsResponse(BaseModel):
    """Schema for system settings response"""
    auto_notification_enabled: bool
    notification_interval_seconds: int
    hospital_search_radius_km: float
    max_hospitals_to_notify: int
    max_notification_retries: int
    maintenance_mode: bool
    test_mode: bool
    updated_at: datetime


class MaintenanceModeRequest(BaseModel):
    """Schema for maintenance mode request"""
    enabled: bool = Field(..., description="Enable or disable maintenance mode")
    reason: Optional[str] = Field(None, max_length=500)
    scheduled_end_time: Optional[datetime] = None


class MaintenanceModeResponse(BaseModel):
    """Schema for maintenance mode response"""
    maintenance_mode: bool
    reason: Optional[str] = None
    started_at: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    message: str


class SystemHealthResponse(BaseModel):
    """Schema for system health check response"""
    status: str
    timestamp: datetime
    database_connected: bool
    scheduler_running: bool
    active_incidents: int
    pending_notifications: int
    online_cameras: int
    maintenance_mode: bool
    uptime_seconds: float


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    method: Optional[str] = None
    endpoint: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class EmergencyStopRequest(BaseModel):
    """Schema for emergency stop request"""
    reason: str = Field(..., min_length=10, max_length=500)
    stop_scope: str = Field("all", description="Scope: 'all' or 'incident_id'")
    incident_id: Optional[UUID] = None


class EmergencyStopResponse(BaseModel):
    """Schema for emergency stop response"""
    stopped_count: int
    incidents_affected: List[UUID]
    timestamp: datetime
    message: str


# ─── Emergency Contact Notification Settings (NEW) ────────────────────────────

class NotificationSettingsUpdate(BaseModel):
    """Schema for updating emergency contact notification settings"""
    emergency_contact_number: Optional[str] = Field(
        None,
        description="Phone number in E.164 format, e.g. +919876543210",
        max_length=20,
    )
    emergency_notifications_enabled: Optional[bool] = Field(
        None,
        description="Enable/disable emergency SMS notifications to the contact number",
    )
    hospital_notifications_enabled: Optional[bool] = Field(
        None,
        description="Enable/disable hospital notifications (informational; feature is off by default)",
    )


class NotificationSettingsResponse(BaseModel):
    """Schema for notification settings response"""
    emergency_contact_number: Optional[str] = None
    emergency_notifications_enabled: bool
    hospital_notifications_enabled: bool
    updated_at: datetime


class TestNotificationResponse(BaseModel):
    """Schema for test notification response"""
    sent: bool
    message: str
    recipient: Optional[str] = None
    provider: Optional[str] = None
    timestamp: datetime


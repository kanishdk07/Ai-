"""
Notification Schemas
Pydantic models for notification-related requests and responses
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from app.models.notification import NotificationType, NotificationStatus, RecipientType


class NotificationBase(BaseModel):
    """Base notification schema"""
    incident_id: UUID
    notification_type: NotificationType
    message: str


class ManualNotificationRequest(BaseModel):
    """Schema for manual notification request"""
    incident_id: str = Field(..., description="Incident ID or UUID to notify about")
    recipient_phone: Optional[str] = Field(None, description="Phone number in international format (e.g., +919876543210)")
    recipient_email: Optional[EmailStr] = None
    recipient_name: Optional[str] = None
    hospital_id: Optional[str] = Field(None, description="Hospital ID to notify (if not manual)")
    notification_type: NotificationType = NotificationType.SMS
    custom_message: Optional[str] = Field(None, max_length=500, description="Optional custom message")
    incident_source: Optional[str] = Field("live_camera", description="live_camera or uploaded_video")
    latitude: Optional[float] = Field(None, description="Verified latitude")
    longitude: Optional[float] = Field(None, description="Verified longitude")
    location_description: Optional[str] = Field(None, description="Human readable location description")


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_id: str
    incident_id: UUID
    recipient_type: RecipientType
    hospital_id: Optional[UUID] = None
    recipient_phone: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None
    notification_type: NotificationType
    status: NotificationStatus
    message: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    retry_count: int
    is_repeat: bool
    repeat_sequence: int
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list"""
    notifications: List[NotificationResponse]
    total: int
    page: int
    page_size: int


class StopNotificationRequest(BaseModel):
    """Schema for stopping notifications"""
    reason: str = Field(..., min_length=5, max_length=500)
    stop_all_for_incident: bool = Field(True, description="Stop all future notifications for this incident")

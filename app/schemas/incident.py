"""
Incident Schemas
Pydantic models for incident-related requests and responses
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from app.models.incident import SeverityLevel, IncidentStatus


class VehicleInfo(BaseModel):
    """Vehicle information schema"""
    vehicle_type: Optional[str] = None
    count: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class IncidentBase(BaseModel):
    """Base incident schema"""
    incident_id: str = Field(..., min_length=1, max_length=100, description="Unique incident identifier from AI module")
    camera_external_id: Optional[str] = Field(None, description="Camera ID from AI module")
    detected_at: datetime = Field(..., description="Timestamp when accident was detected")
    accident_detected: bool = Field(True, description="Whether accident was detected")
    severity: SeverityLevel = Field(..., description="Accident severity level")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence score (0.0-1.0)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Accident latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Accident longitude")
    location_description: Optional[str] = Field(None, max_length=500)


class IncidentCreate(IncidentBase):
    """Schema for creating incident (AI integration endpoint)"""
    accident_image_url: Optional[str] = Field(None, max_length=500)
    vehicle_count: Optional[int] = Field(0, ge=0)
    vehicle_info: Optional[Dict[str, Any]] = None
    ai_event_data: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = Field(None, description="Idempotency key to prevent duplicate events")


class IncidentUpdate(BaseModel):
    """Schema for updating incident"""
    severity: Optional[SeverityLevel] = None
    status: Optional[IncidentStatus] = None
    location_description: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IncidentResponse(IncidentBase):
    """Schema for incident response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    camera_id: Optional[UUID] = None
    status: IncidentStatus
    accident_image_url: Optional[str] = None
    vehicle_count: Optional[int] = None
    vehicle_info: Optional[Dict[str, Any]] = None
    ai_event_data: Optional[Dict[str, Any]] = None
    notification_started_at: Optional[datetime] = None
    notification_stopped_at: Optional[datetime] = None
    notification_count: int
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_hospital_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class IncidentListResponse(BaseModel):
    """Schema for paginated incident list"""
    incidents: List[IncidentResponse]
    total: int
    page: int
    page_size: int


class IncidentAcknowledgeRequest(BaseModel):
    """Schema for incident acknowledgment"""
    hospital_id: Optional[UUID] = None
    acknowledgment_token: Optional[str] = Field(None, description="Secure token from notification link")
    notes: Optional[str] = None
    responder_name: Optional[str] = None


class IncidentAcknowledgeResponse(BaseModel):
    """Schema for acknowledgment response"""
    incident_id: UUID
    status: IncidentStatus
    acknowledged_at: datetime
    hospital_name: Optional[str] = None
    message: str


class IncidentResolveRequest(BaseModel):
    """Schema for resolving incident"""
    resolution_notes: str = Field(..., min_length=10, max_length=2000)
    outcome: Optional[str] = None


class IncidentCancelRequest(BaseModel):
    """Schema for cancelling incident"""
    reason: str = Field(..., min_length=5, max_length=500)

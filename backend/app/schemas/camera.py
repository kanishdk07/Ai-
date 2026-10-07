"""
Camera Schemas
Pydantic models for camera-related requests and responses
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.camera import CameraType, CameraStatus


class CameraBase(BaseModel):
    """Base camera schema"""
    camera_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    camera_type: CameraType
    location_name: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    description: Optional[str] = None


class CameraCreate(CameraBase):
    """Schema for creating a new camera"""
    connection_config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class CameraUpdate(BaseModel):
    """Schema for updating camera"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location_name: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    connection_config: Optional[Dict[str, Any]] = None
    status: Optional[CameraStatus] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CameraResponse(CameraBase):
    """Schema for camera response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: CameraStatus
    is_monitoring: bool
    health_score: Optional[int] = None
    last_active_at: Optional[datetime] = None
    last_detection_at: Optional[datetime] = None
    total_detections: int
    uptime_percentage: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class CameraListResponse(BaseModel):
    """Schema for paginated camera list"""
    cameras: list[CameraResponse]
    total: int
    page: int
    page_size: int


class CameraActionRequest(BaseModel):
    """Schema for camera action requests (start/stop)"""
    reason: Optional[str] = None

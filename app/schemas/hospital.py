"""
Hospital Schemas
Pydantic models for hospital-related requests and responses
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class HospitalBase(BaseModel):
    """Base hospital schema"""
    name: str = Field(..., min_length=1, max_length=255)
    phone_numbers: List[str] = Field(..., min_items=1, description="List of contact phone numbers")
    email: Optional[EmailStr] = None
    address: str = Field(..., min_length=5)
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class HospitalCreate(HospitalBase):
    """Schema for creating hospital"""
    hospital_code: Optional[str] = None
    emergency_contact: Optional[str] = None
    has_emergency_dept: bool = True
    has_trauma_center: bool = False
    has_ambulance: bool = True
    bed_capacity: Optional[int] = None
    is_24_7: bool = True
    accepts_sms: bool = True
    accepts_email: bool = False
    accepts_call: bool = True
    description: Optional[str] = None
    website: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HospitalUpdate(BaseModel):
    """Schema for updating hospital"""
    name: Optional[str] = None
    phone_numbers: Optional[List[str]] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    emergency_contact: Optional[str] = None
    is_available: Optional[bool] = None
    available_beds: Optional[int] = None
    accepts_sms: Optional[bool] = None
    accepts_email: Optional[bool] = None
    accepts_call: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class HospitalResponse(HospitalBase):
    """Schema for hospital response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hospital_code: Optional[str] = None
    emergency_contact: Optional[str] = None
    has_emergency_dept: bool
    has_trauma_center: bool
    has_ambulance: bool
    bed_capacity: Optional[int] = None
    available_beds: Optional[int] = None
    is_available: bool
    is_24_7: bool
    accepts_sms: bool
    accepts_email: bool
    accepts_call: bool
    average_response_time_minutes: Optional[float] = None
    total_responses: int
    successful_responses: int
    description: Optional[str] = None
    website: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_notified_at: Optional[datetime] = None


class NearbyHospitalResponse(HospitalResponse):
    """Schema for nearby hospital with distance"""
    distance_km: float = Field(..., description="Distance from incident location in kilometers")


class HospitalListResponse(BaseModel):
    """Schema for paginated hospital list"""
    hospitals: List[HospitalResponse]
    total: int
    page: int
    page_size: int


class NearbyHospitalsRequest(BaseModel):
    """Schema for finding nearby hospitals"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: Optional[float] = Field(None, gt=0, le=200, description="Search radius in kilometers")
    limit: Optional[int] = Field(10, gt=0, le=50, description="Maximum number of hospitals")

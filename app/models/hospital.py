"""
Hospital Model
Manages hospital/emergency responder information
"""

from sqlalchemy import Column, String, Boolean, DateTime, Float, Text, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Hospital(Base):
    """Hospital/Emergency Responder model"""
    __tablename__ = "hospitals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False)
    hospital_code = Column(String(50), unique=True, nullable=True, index=True)

    # Contact information
    phone_numbers = Column(JSON, nullable=False)  # List of contact numbers
    email = Column(String(255), nullable=True)
    emergency_contact = Column(String(255), nullable=True)

    # Location
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="India", nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # lat/lon stored as Float; spatial queries use Haversine formula

    # Services and capabilities
    has_emergency_dept = Column(Boolean, default=True, nullable=False)
    has_trauma_center = Column(Boolean, default=False, nullable=False)
    has_ambulance = Column(Boolean, default=True, nullable=False)
    bed_capacity = Column(Float, nullable=True)
    available_beds = Column(Float, nullable=True)

    # Service availability
    is_available = Column(Boolean, default=True, nullable=False)
    is_24_7 = Column(Boolean, default=True, nullable=False)

    # Notification preferences
    accepts_sms = Column(Boolean, default=True, nullable=False)
    accepts_email = Column(Boolean, default=False, nullable=False)
    accepts_call = Column(Boolean, default=True, nullable=False)

    # Performance metrics
    average_response_time_minutes = Column(Float, nullable=True)
    total_responses = Column(Float, default=0, nullable=False)
    successful_responses = Column(Float, default=0, nullable=False)

    # Additional information
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    meta_data = Column("metadata", JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    last_notified_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Hospital {self.name} - {self.city}>"

    @property
    def primary_phone(self) -> str:
        """Get primary phone number"""
        phones = self.phone_numbers
        if isinstance(phones, list):
            return phones[0] if phones else None
        return None

    @property
    def can_receive_notifications(self) -> bool:
        """Check if hospital can receive notifications"""
        return self.is_active and self.is_available and (
            self.accepts_sms or self.accepts_email or self.accepts_call
        )

    @property
    def response_rate(self) -> float:
        """Calculate response success rate"""
        if self.total_responses == 0:
            return 0.0
        return (self.successful_responses / self.total_responses) * 100

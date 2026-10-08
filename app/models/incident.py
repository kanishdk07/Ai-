"""
Incident Model
Handles accident detection events and incident lifecycle
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Text, Float, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class SeverityLevel(str, enum.Enum):
    """Incident severity levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, enum.Enum):
    """Incident lifecycle status"""
    DETECTED = "detected"
    AWAITING_REVIEW = "awaiting_review"
    ACTIVE = "active"
    NOTIFICATION_PENDING = "notification_pending"
    NOTIFIED = "notified"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class Incident(Base):
    """Incident model for detected accidents"""
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    incident_id = Column(String(100), unique=True, nullable=False, index=True)

    # Camera reference
    camera_id = Column(String(36), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    camera_external_id = Column(String(100), nullable=True)  # AI module's camera ID

    # Detection details
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    accident_detected = Column(Boolean, default=True, nullable=False)
    severity = Column(SQLEnum(SeverityLevel), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_description = Column(String(500), nullable=True)

    # Vehicle information
    vehicle_count = Column(Integer, default=0, nullable=True)
    vehicle_info = Column(JSON, nullable=True)  # Detailed vehicle data from AI

    # Media
    accident_image_url = Column(String(500), nullable=True)
    additional_media = Column(JSON, nullable=True)

    # AI event details
    ai_event_data = Column(JSON, nullable=True)

    # Status and lifecycle
    status = Column(SQLEnum(IncidentStatus), nullable=False, default=IncidentStatus.DETECTED, index=True)

    # Notification tracking
    notification_started_at = Column(DateTime(timezone=True), nullable=True)
    notification_stopped_at = Column(DateTime(timezone=True), nullable=True)
    notification_count = Column(Integer, default=0, nullable=False)

    # Acknowledgment details
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by_hospital_id = Column(String(36), nullable=True)
    acknowledgment_details = Column(JSON, nullable=True)

    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(36), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)
    meta_data = Column("metadata", JSON, nullable=True)

    # Idempotency
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<Incident {self.incident_id} - {self.severity} - {self.status}>"

    @property
    def is_active(self) -> bool:
        """Check if incident is in active state"""
        return self.status in [
            IncidentStatus.ACTIVE,
            IncidentStatus.NOTIFICATION_PENDING,
            IncidentStatus.NOTIFIED
        ]

    @property
    def can_notify(self) -> bool:
        """Check if incident can trigger notifications"""
        return self.status in [
            IncidentStatus.DETECTED,
            IncidentStatus.ACTIVE,
            IncidentStatus.NOTIFICATION_PENDING,
            IncidentStatus.NOTIFIED
        ]

    @property
    def needs_acknowledgment(self) -> bool:
        """Check if incident is waiting for acknowledgment"""
        return self.status == IncidentStatus.NOTIFIED

    @property
    def is_closed(self) -> bool:
        """Check if incident is closed"""
        return self.status in [IncidentStatus.RESOLVED, IncidentStatus.CANCELLED]

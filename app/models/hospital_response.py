"""
Hospital Response Model
Stores and tracks hospital and responder acknowledgment responses
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class ResponseType(str, enum.Enum):
    """Response type enumeration"""
    WEB = "web"
    SMS_WEBHOOK = "sms_webhook"
    PHONE_CALL = "phone_call"
    FCM_APP = "fcm_app"
    MANUAL = "manual"


class VerificationStatus(str, enum.Enum):
    """Verification status enumeration"""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"


class HospitalResponse(Base):
    """Hospital Response model for incident acknowledgments"""
    __tablename__ = "hospital_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    response_id = Column(String(100), unique=True, nullable=False, index=True)

    # Incident and Hospital reference
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True, index=True)
    verified_recipient_ref = Column(String(255), nullable=True)  # Phone number, email, or credential ref

    # Response details
    response_type = Column(String(50), nullable=False, default=ResponseType.WEB.value)
    response_timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    verification_status = Column(String(50), nullable=False, default=VerificationStatus.VERIFIED.value)

    # Additional notes & responder details
    responder_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    raw_payload = Column(JSON, nullable=True)

    # Metadata
    meta_data = Column("metadata", JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<HospitalResponse {self.response_id} - Incident {self.incident_id} - {self.verification_status}>"

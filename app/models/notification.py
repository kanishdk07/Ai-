"""
Notification Model
Tracks emergency notifications sent to hospitals
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Text, Float, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class NotificationType(str, enum.Enum):
    """Notification type enumeration"""
    SMS = "sms"
    EMAIL = "email"
    CALL = "call"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationStatus(str, enum.Enum):
    """Notification status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"
    CANCELLED = "cancelled"


class RecipientType(str, enum.Enum):
    """Recipient type enumeration"""
    HOSPITAL = "hospital"
    MANUAL = "manual"
    EXTERNAL = "external"


class Notification(Base):
    """Notification model for tracking emergency alerts"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    notification_id = Column(String(100), unique=True, nullable=False, index=True)

    # Incident reference
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Recipient information
    recipient_type = Column(SQLEnum(RecipientType), nullable=False, default=RecipientType.HOSPITAL)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    recipient_phone = Column(String(20), nullable=True)
    recipient_email = Column(String(255), nullable=True)
    recipient_name = Column(String(255), nullable=True)

    # Notification details
    notification_type = Column(SQLEnum(NotificationType), nullable=False, default=NotificationType.SMS)
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True)

    # Message content
    message = Column(Text, nullable=False)
    subject = Column(String(255), nullable=True)

    # Sending details
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Response tracking
    response_data = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    error_message = Column(Text, nullable=True)

    # Provider details
    provider = Column(String(50), nullable=True)  # twilio, sendgrid, etc.
    provider_message_id = Column(String(255), nullable=True)
    provider_response = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)

    # Repeat notification tracking
    is_repeat = Column(Boolean, default=False, nullable=False)
    repeat_sequence = Column(Integer, default=1, nullable=False)
    parent_notification_id = Column(UUID(as_uuid=True), nullable=True)

    # Job tracking
    job_id = Column(String(255), nullable=True, index=True)

    # Metadata
    meta_data = Column("metadata", JSON().with_variant(JSONB(), "postgresql"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<Notification {self.notification_id} - {self.notification_type} - {self.status}>"

    @property
    def can_retry(self) -> bool:
        """Check if notification can be retried"""
        return (
            self.status == NotificationStatus.FAILED
            and self.retry_count < self.max_retries
        )

    @property
    def is_successful(self) -> bool:
        """Check if notification was successfully delivered"""
        return self.status in [NotificationStatus.DELIVERED, NotificationStatus.ACKNOWLEDGED]

    @property
    def is_completed(self) -> bool:
        """Check if notification lifecycle is complete"""
        return self.status in [
            NotificationStatus.DELIVERED,
            NotificationStatus.ACKNOWLEDGED,
            NotificationStatus.CANCELLED
        ]

"""
Accident Image Model
Stores image metadata and storage references without raw binary in relational DB fields
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class ImageVerificationStatus(str, enum.Enum):
    """Image verification status enumeration"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class AccidentImage(Base):
    """Accident Image model for managing accident media metadata"""
    __tablename__ = "accident_images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    image_id = Column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    camera_id = Column(String(36), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True, index=True)

    # Metadata & storage reference
    capture_timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    storage_reference = Column(String(500), nullable=False)  # Local file path, relative URL, or Object Storage key
    file_type = Column(String(50), nullable=False, default="image/jpeg")
    file_size_bytes = Column(Integer, nullable=True)
    image_verification_status = Column(String(50), nullable=False, default=ImageVerificationStatus.PENDING.value)

    # Protection & access controls
    is_protected = Column(String(10), default="true", nullable=False)

    # Additional metadata
    meta_data = Column("metadata", JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AccidentImage {self.image_id} - Incident {self.incident_id} - {self.image_verification_status}>"

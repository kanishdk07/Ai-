"""
Camera Model
Handles camera registration and monitoring
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Text, Integer, Float, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum

# Use PostgreSQL UUID type if available, else String
try:
    from sqlalchemy.dialects.postgresql import UUID
    _UUID = UUID(as_uuid=True)
except Exception:
    _UUID = String(36)


class CameraType(str, enum.Enum):
    """Camera type enumeration"""
    SYSTEM = "system"
    MOBILE = "mobile"
    IP_CCTV = "ip_cctv"
    EXTERNAL = "external"


class CameraStatus(str, enum.Enum):
    """Camera status enumeration"""
    ONLINE = "online"
    OFFLINE = "offline"
    MONITORING = "monitoring"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class Camera(Base):
    """Camera model for managing detection cameras"""
    __tablename__ = "cameras"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    camera_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    camera_type = Column(SQLEnum(CameraType), nullable=False, default=CameraType.SYSTEM)

    # Location
    location_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    # lat/lon stored as Float; spatial queries use Haversine formula

    # Connection configuration
    connection_config = Column(JSON, nullable=True)

    # Status and health
    status = Column(SQLEnum(CameraStatus), nullable=False, default=CameraStatus.OFFLINE)
    is_monitoring = Column(Boolean, default=False, nullable=False)
    health_score = Column(Integer, default=100, nullable=True)  # 0-100

    # Monitoring statistics
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    last_detection_at = Column(DateTime(timezone=True), nullable=True)
    total_detections = Column(Integer, default=0, nullable=False)
    uptime_percentage = Column(Float, default=0.0, nullable=True)

    # Additional metadata
    description = Column(Text, nullable=True)
    meta_data = Column("metadata", JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    created_by = Column(String(36), nullable=True)

    def __repr__(self):
        return f"<Camera {self.camera_id} ({self.camera_type}) - {self.status}>"

    @property
    def is_healthy(self) -> bool:
        """Check if camera is healthy (health score > 70)"""
        return self.health_score and self.health_score > 70

    @property
    def can_monitor(self) -> bool:
        """Check if camera can be used for monitoring"""
        return self.status not in [CameraStatus.ERROR, CameraStatus.MAINTENANCE] and self.is_healthy

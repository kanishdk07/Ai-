"""
Admin Setting Model
Persists system configuration, repeat intervals, and maintenance mode settings
"""

from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid


class AdminSetting(Base):
    """Admin Settings model for persistent system configuration"""
    __tablename__ = "admin_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Core settings
    auto_notification_enabled = Column(Boolean, default=False, nullable=False)
    notification_repeat_interval = Column(Integer, default=60, nullable=False)  # 30-300 seconds
    maintenance_mode = Column(Boolean, default=False, nullable=False)
    monitoring_status = Column(String(50), default="active", nullable=False)
    default_hospital_search_radius = Column(Float, default=50.0, nullable=False)

    # System version and audit
    system_configuration_version = Column(Integer, default=1, nullable=False)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Additional metadata
    extra_config = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)

    # Timestamps
    last_updated_timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AdminSetting v{self.system_configuration_version} - AutoNotify: {self.auto_notification_enabled} - Maintenance: {self.maintenance_mode}>"

"""
Audit Log Model
Tracks all administrative actions and system events
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid


class AuditLog(Base):
    """Audit log model for tracking system events"""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    # User who performed the action
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(100), nullable=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)  # incident, camera, notification, etc.
    resource_id = Column(String(255), nullable=True, index=True)

    # Request details
    method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    endpoint = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Change tracking
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Result
    success = Column(String(10), default="true", nullable=False)
    error_message = Column(Text, nullable=True)

    # Additional context
    description = Column(Text, nullable=True)
    meta_data = Column("metadata", JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username} at {self.created_at}>"

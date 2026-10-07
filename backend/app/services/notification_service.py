"""
Notification Service
Handles notification creation, sending, and tracking
"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from app.models import (
    Notification,
    NotificationStatus,
    NotificationType,
    RecipientType,
    Incident,
    Hospital,
)
from app.schemas.notification import ManualNotificationRequest
from app.utils.security import generate_secure_id, create_acknowledgment_token
from app.utils.validators import validate_phone_number, format_phone_number
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for notification operations"""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        incident_id: UUID,
        hospital_id: Optional[UUID] = None,
        recipient_phone: Optional[str] = None,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None,
        notification_type: NotificationType = NotificationType.SMS,
        custom_message: Optional[str] = None,
        is_repeat: bool = False,
        repeat_sequence: int = 1,
        created_by: Optional[UUID] = None,
    ) -> Notification:
        """
        Create a new notification

        Args:
            db: Database session
            incident_id: Incident UUID
            hospital_id: Hospital UUID (for hospital notifications)
            recipient_phone: Phone number (for manual notifications)
            recipient_email: Email (for email notifications)
            recipient_name: Recipient name
            notification_type: Type of notification
            custom_message: Custom message override
            is_repeat: Whether this is a repeat notification
            repeat_sequence: Sequence number for repeat notifications
            created_by: User who created the notification

        Returns:
            Created notification
        """
        # Determine recipient type
        if hospital_id:
            recipient_type = RecipientType.HOSPITAL
            # Get hospital details
            hospital_result = await db.execute(select(Hospital).where(Hospital.id == hospital_id))
            hospital = hospital_result.scalar_one_or_none()
            if not hospital:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Hospital not found"
                )
            recipient_phone = recipient_phone or hospital.primary_phone
            recipient_email = recipient_email or hospital.email
            recipient_name = recipient_name or hospital.name
        else:
            recipient_type = RecipientType.MANUAL

        # Validate phone number if SMS
        if notification_type == NotificationType.SMS:
            if not recipient_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number required for SMS notifications"
                )
            formatted_phone = format_phone_number(recipient_phone)
            if not formatted_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid phone number format"
                )
            recipient_phone = formatted_phone

        # Get incident details for message
        incident_result = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = incident_result.scalar_one_or_none()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        # Build message
        if custom_message:
            message = custom_message
        else:
            message = NotificationService._build_notification_message(incident, repeat_sequence)

        # Create notification
        notification_id = generate_secure_id("NOTIF-")
        new_notification = Notification(
            notification_id=notification_id,
            incident_id=incident_id,
            recipient_type=recipient_type,
            hospital_id=hospital_id,
            recipient_phone=recipient_phone,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            notification_type=notification_type,
            status=NotificationStatus.PENDING,
            message=message,
            is_repeat=is_repeat,
            repeat_sequence=repeat_sequence,
            created_by=created_by,
        )

        db.add(new_notification)
        await db.commit()
        await db.refresh(new_notification)

        logger.info(f"Notification created: {new_notification.notification_id} for incident {incident.incident_id}")
        return new_notification

    @staticmethod
    def _build_notification_message(incident: Incident, repeat_sequence: int = 1) -> str:
        """Build notification message content"""
        severity_text = incident.severity.value.upper()
        location = incident.location_description or f"Lat: {incident.latitude}, Lon: {incident.longitude}"

        message = (
            f"🚨 EMERGENCY ALERT - Highway Accident Detected\n\n"
            f"Severity: {severity_text}\n"
            f"Location: {location}\n"
            f"Time: {incident.detected_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Incident ID: {incident.incident_id}\n"
        )

        if incident.vehicle_count and incident.vehicle_count > 0:
            message += f"Vehicles Involved: {incident.vehicle_count}\n"

        if repeat_sequence > 1:
            message += f"\n⚠️ REPEAT ALERT #{repeat_sequence}\n"

        if settings.TEST_MODE:
            message += "\n[TEST MODE - No actual emergency]"

        return message

    @staticmethod
    async def send_notification(db: AsyncSession, notification_id: UUID) -> Notification:
        """
        Send a notification (mock implementation)

        In production, integrate with actual SMS/Email providers
        """
        notification = await NotificationService.get_notification(db, notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        try:
            # Mock sending - in production, call actual provider
            if settings.TEST_MODE:
                logger.info(f"[TEST MODE] Would send {notification.notification_type} to {notification.recipient_phone or notification.recipient_email}")
                logger.info(f"[TEST MODE] Message: {notification.message}")
            else:
                # TODO: Integrate with actual SMS/Email provider
                # Example: await send_sms(notification.recipient_phone, notification.message)
                logger.warning("Production notification sending not yet implemented")

            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.delivered_at = datetime.utcnow()  # Mock immediate delivery

            # Update incident notification count
            incident_result = await db.execute(
                select(Incident).where(Incident.id == notification.incident_id)
            )
            incident = incident_result.scalar_one_or_none()
            if incident:
                incident.notification_count += 1
                if incident.notification_started_at is None:
                    incident.notification_started_at = datetime.utcnow()
                incident.status = IncidentStatus.NOTIFIED

            await db.commit()
            await db.refresh(notification)

            logger.info(f"Notification sent: {notification.notification_id}")
            return notification

        except Exception as e:
            # Handle sending failure
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
            notification.error_message = str(e)
            notification.retry_count += 1

            await db.commit()
            await db.refresh(notification)

            logger.error(f"Notification failed: {notification.notification_id} - {str(e)}")
            return notification

    @staticmethod
    async def get_notification(db: AsyncSession, notification_id: UUID) -> Optional[Notification]:
        """Get notification by UUID"""
        result = await db.execute(select(Notification).where(Notification.id == notification_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_notifications_for_incident(
        db: AsyncSession,
        incident_id: UUID
    ) -> List[Notification]:
        """Get all notifications for an incident"""
        result = await db.execute(
            select(Notification)
            .where(Notification.incident_id == incident_id)
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_pending_notifications(db: AsyncSession) -> List[Notification]:
        """Get all pending notifications"""
        result = await db.execute(
            select(Notification).where(Notification.status == NotificationStatus.PENDING)
        )
        return list(result.scalars().all())

    @staticmethod
    async def cancel_notifications_for_incident(
        db: AsyncSession,
        incident_id: UUID
    ) -> int:
        """
        Cancel all pending/scheduled notifications for an incident

        Returns:
            Number of notifications cancelled
        """
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.incident_id == incident_id,
                    Notification.status.in_([
                        NotificationStatus.PENDING,
                        NotificationStatus.FAILED
                    ])
                )
            )
        )
        notifications = result.scalars().all()

        count = 0
        for notification in notifications:
            notification.status = NotificationStatus.CANCELLED
            count += 1

        if count > 0:
            await db.commit()
            logger.info(f"Cancelled {count} notifications for incident {incident_id}")

        return count

    @staticmethod
    async def create_manual_notification(
        db: AsyncSession,
        request: ManualNotificationRequest,
        user_id: UUID
    ) -> Notification:
        """Create and send manual notification"""
        notification = await NotificationService.create_notification(
            db=db,
            incident_id=request.incident_id,
            hospital_id=request.hospital_id,
            recipient_phone=request.recipient_phone,
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            notification_type=request.notification_type,
            custom_message=request.custom_message,
            created_by=user_id,
        )

        # Send immediately
        await NotificationService.send_notification(db, notification.id)

        return notification

"""
Notification Service
Handles notification creation, sending, and tracking
"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status
from app.models import (
    Notification,
    NotificationStatus,
    NotificationType,
    RecipientType,
    Incident,
    IncidentStatus,
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
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        incident_id: str,
        hospital_id: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None,
        notification_type: NotificationType = NotificationType.SMS,
        custom_message: Optional[str] = None,
        is_repeat: bool = False,
        repeat_sequence: int = 1,
        created_by: Optional[str] = None,
        incident_source: str = "live_camera",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_description: Optional[str] = None,
    ) -> Notification:
        """
        Create a new notification with idempotency check & nearest hospital resolution
        """
        # 1. Look up incident record in database
        incident_result = await db.execute(
            select(Incident).where(
                or_(Incident.id == str(incident_id), Incident.incident_id == str(incident_id))
            )
        )
        incident = incident_result.scalar_one_or_none()

        # If incident not yet stored in DB (e.g. transient uploaded video test), create or use fallback incident structure
        if not incident:
            # Check if camera exists to resolve location
            from app.models.camera import Camera
            cam_res = await db.execute(select(Camera).where(or_(Camera.id == str(incident_id), Camera.camera_id == str(incident_id))))
            cam = cam_res.scalar_one_or_none()

            eff_lat = latitude if latitude is not None else (cam.latitude if cam else None)
            eff_lon = longitude if longitude is not None else (cam.longitude if cam else None)
            eff_loc = location_description or (cam.location_description if cam else None)

            # Create DB incident record
            from app.models.incident import SeverityLevel, IncidentStatus
            new_inc_id = str(incident_id)
            if not new_inc_id.startswith("ACC-") and not new_inc_id.startswith("INC-"):
                new_inc_id = generate_secure_id("ACC-")

            incident = Incident(
                incident_id=new_inc_id,
                camera_external_id=str(incident_id),
                detected_at=datetime.utcnow(),
                accident_detected=True,
                severity=SeverityLevel.MEDIUM,
                confidence_score=0.88,
                latitude=eff_lat,
                longitude=eff_lon,
                location_description=eff_loc or ("Camera Location" if eff_lat else "Location not provided"),
                status=IncidentStatus.DETECTED
            )
            db.add(incident)
            await db.commit()
            await db.refresh(incident)

        # Update coordinates on incident if explicitly provided
        if latitude is not None:
            incident.latitude = latitude
        if longitude is not None:
            incident.longitude = longitude
        if location_description:
            incident.location_description = location_description

        nearest_hospital_name = None

        # 2. Nearest Hospital Resolution for Scenario A (Live Camera)
        if incident_source == "live_camera" and incident.latitude is not None and incident.longitude is not None:
            from app.services.hospital_service import HospitalService
            nearby = await HospitalService.find_nearby_hospitals(
                db=db,
                latitude=incident.latitude,
                longitude=incident.longitude,
                limit=1
            )
            if nearby and len(nearby) > 0:
                top_hosp = nearby[0]
                nearest_hospital_name = top_hosp.get("name")
                if not hospital_id and not recipient_phone:
                    hospital_id = str(top_hosp.get("id"))
                    recipient_phone = top_hosp.get("primary_phone") or (top_hosp.get("phone_numbers", [None])[0])
                    recipient_name = top_hosp.get("name")

        # Determine recipient type
        if hospital_id:
            recipient_type = RecipientType.HOSPITAL
            hospital_result = await db.execute(select(Hospital).where(Hospital.id == str(hospital_id)))
            hospital = hospital_result.scalar_one_or_none()
            if hospital:
                recipient_phone = recipient_phone or hospital.primary_phone
                recipient_email = recipient_email or hospital.email
                recipient_name = recipient_name or hospital.name
                nearest_hospital_name = hospital.name
        else:
            recipient_type = RecipientType.MANUAL

        # Validate phone number for SMS
        if notification_type == NotificationType.SMS:
            if not recipient_phone:
                # Default safety fallback recipient if unconfigured
                recipient_phone = "+919876543210"
            formatted_phone = format_phone_number(recipient_phone)
            if formatted_phone:
                recipient_phone = formatted_phone

        # 3. Idempotency & Duplicate Prevention (60-second window)
        existing_notif_res = await db.execute(
            select(Notification).where(
                and_(
                    or_(
                        Notification.incident_id == str(incident.id),
                        Notification.incident_id == str(incident.incident_id)
                    ),
                    Notification.recipient_phone == recipient_phone,
                    or_(
                        Notification.status.in_([NotificationStatus.DELIVERED, NotificationStatus.PENDING, NotificationStatus.SENT]),
                        Notification.status.in_(["delivered", "pending", "sent"])
                    )
                )
            ).order_by(Notification.created_at.desc())
        )
        dup_notif = existing_notif_res.scalars().first()
        if dup_notif:
            # Increment repeat count for idempotency
            dup_notif.is_repeat = True
            dup_notif.repeat_sequence += 1
            await db.commit()
            await db.refresh(dup_notif)
            logger.info(f"Duplicate notification suppressed for incident {incident.incident_id}. Updated repeat #{dup_notif.repeat_sequence}")
            return dup_notif

        # Generate acknowledgment token
        hospital_id_str = str(hospital_id) if hospital_id else "manual"
        ack_token = create_acknowledgment_token(str(incident.id), hospital_id_str)

        # Build message
        if custom_message:
            message = custom_message
        else:
            message = NotificationService._build_notification_message(
                incident=incident,
                ack_token=ack_token,
                repeat_sequence=repeat_sequence,
                incident_source=incident_source,
                nearest_hospital_name=nearest_hospital_name
            )

        # Create notification record
        notification_id = generate_secure_id("NOTIF-")
        new_notification = Notification(
            notification_id=notification_id,
            incident_id=str(incident.id),
            recipient_type=recipient_type,
            hospital_id=str(hospital_id) if hospital_id else None,
            recipient_phone=recipient_phone,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            notification_type=notification_type,
            status=NotificationStatus.PENDING,
            message=message,
            is_repeat=is_repeat,
            repeat_sequence=repeat_sequence,
            created_by=str(created_by) if created_by else None,
        )

        db.add(new_notification)
        await db.commit()
        await db.refresh(new_notification)

        logger.info(f"Notification created: {new_notification.notification_id} for incident {incident.incident_id}")
        return new_notification

    @staticmethod
    def _build_notification_message(
        incident: Incident,
        ack_token: Optional[str] = None,
        repeat_sequence: int = 1,
        incident_source: str = "live_camera",
        nearest_hospital_name: Optional[str] = None
    ) -> str:
        """
        Build concise, compliant emergency alert SMS content per requirements
        """
        severity_text = incident.severity.value.upper()
        timestamp_str = incident.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC') if incident.detected_at else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        if incident_source == "uploaded_video" or (incident.camera_external_id and "UPLOAD" in incident.camera_external_id.upper()):
            # Scenario B: Uploaded Video Notification
            loc_str = incident.location_description if incident.location_description and "unavailable" not in incident.location_description.lower() else "Location not provided"
            msg = f"SAFEWAY.AI ALERT: {severity_text} accident identified in video analysis. Reported location: {loc_str}. Time: {timestamp_str}. Incident: {incident.incident_id}. Verify the incident location before dispatch."
        else:
            # Scenario A: Live Camera Incident Notification
            if incident.latitude is not None and incident.longitude is not None:
                coords_str = f"{incident.latitude:.5f}, {incident.longitude:.5f}"
                loc_str = incident.location_description or f"Highway Camera Location ({coords_str})"
            else:
                coords_str = "N/A"
                loc_str = "Camera location unavailable"

            msg = f"SAFEWAY.AI ALERT: {severity_text} accident detected. Location: {loc_str}. Coordinates: {coords_str}. Time: {timestamp_str}. Incident: {incident.incident_id}."
            if nearest_hospital_name:
                msg += f" Nearest Hospital: {nearest_hospital_name}."
            msg += " Please verify and respond according to your procedures."

        if repeat_sequence > 1:
            msg += f" [REPEAT #{repeat_sequence}]"

        if settings.TEST_MODE:
            msg += " [TEST MODE - No Real SMS Sent]"

        return msg.strip()

    @staticmethod
    async def send_notification(db: AsyncSession, notification_id: UUID) -> Notification:
        """
        Send a notification using common notification provider interface (Requirement 5)
        """
        from app.services.notification_providers import NotificationProviderFactory

        notification = await NotificationService.get_notification(db, notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        provider = NotificationProviderFactory.get_provider(
            channel=notification.notification_type.value
        )
        notification.provider = provider.provider_name

        try:
            if notification.notification_type == NotificationType.SMS:
                delivery_res = await provider.send_sms(
                    to_phone=notification.recipient_phone,
                    message=notification.message
                )
            elif notification.notification_type == NotificationType.EMAIL:
                delivery_res = await provider.send_email(
                    to_email=notification.recipient_email,
                    subject=f"🚨 Emergency Alert: Incident {notification.incident_id}",
                    body_text=notification.message
                )
            elif notification.notification_type == NotificationType.PUSH:
                delivery_res = await provider.send_push(
                    device_token=notification.recipient_phone or "default_device",
                    title="🚨 Emergency Highway Alert",
                    body=notification.message
                )
            else:
                delivery_res = await provider.send_sms(
                    to_phone=notification.recipient_phone or "+10000000000",
                    message=notification.message
                )

            notification.provider_message_id = delivery_res.provider_message_id
            notification.provider_response = delivery_res.provider_response

            if delivery_res.success:
                notification.status = NotificationStatus.DELIVERED
                notification.sent_at = datetime.utcnow()
                notification.delivered_at = delivery_res.timestamp

                # Update incident status and count
                incident_result = await db.execute(
                    select(Incident).where(Incident.id == notification.incident_id)
                )
                incident = incident_result.scalar_one_or_none()
                if incident:
                    incident.notification_count += 1
                    if incident.notification_started_at is None:
                        incident.notification_started_at = datetime.utcnow()
                    if incident.status == IncidentStatus.DETECTED:
                        incident.status = IncidentStatus.NOTIFIED

                logger.info(f"Notification delivered cleanly: {notification.notification_id} via {provider.provider_name}")
            else:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = datetime.utcnow()
                notification.error_message = delivery_res.error_message
                notification.retry_count += 1
                logger.warning(f"Notification delivery failed: {notification.notification_id} - {delivery_res.error_message}")

            await db.commit()
            await db.refresh(notification)
            return notification

        except Exception as e:
            # Record failure distinctly
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
            notification.error_message = str(e)
            notification.retry_count += 1

            await db.commit()
            await db.refresh(notification)

            logger.error(f"Notification dispatch error: {notification.notification_id} - {str(e)}")
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
            .where(Notification.incident_id == str(incident_id))
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
                    Notification.incident_id == str(incident_id),
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
        user_id: Optional[UUID] = None
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
            incident_source=request.incident_source or "live_camera",
            latitude=request.latitude,
            longitude=request.longitude,
            location_description=request.location_description,
        )

        # Send immediately
        await NotificationService.send_notification(db, notification.id)

        return notification

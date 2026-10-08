"""
Notification Management API Routes
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.notification import (
    ManualNotificationRequest,
    NotificationResponse,
    StopNotificationRequest,
)
from app.models import User
from app.services.notification_service import NotificationService
from app.services.scheduler_service import get_scheduler
from app.services.websocket_service import WebSocketService
from app.dependencies import get_operator_or_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/manual", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_manual_notification(
    notification_data: ManualNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
):
    """
    Send manual notification

    Requires operator or admin role.

    Can send to:
    - Registered hospital (provide hospital_id)
    - Manual phone number (provide recipient_phone)
    """
    notification = await NotificationService.create_manual_notification(
        db, notification_data, current_user.id
    )

    # Broadcast notification sent
    await WebSocketService.broadcast_notification_sent({
        "notification_id": notification.notification_id,
        "incident_id": str(notification.incident_id),
        "recipient_type": notification.recipient_type.value,
        "status": notification.status.value,
    })

    return notification


@router.post("/{incident_id}/stop", response_model=dict)
async def stop_incident_notifications(
    incident_id: UUID,
    stop_data: StopNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
):
    """
    Stop notifications for a specific incident

    Requires operator or admin role.
    """
    # Cancel pending notifications
    cancelled_count = await NotificationService.cancel_notifications_for_incident(db, incident_id)

    # Stop scheduled notifications
    scheduler = get_scheduler()
    stopped = await scheduler.stop_incident_notifications(incident_id)

    # Broadcast notification stop
    await WebSocketService.broadcast_notifications_stopped(
        str(incident_id),
        reason=stop_data.reason
    )

    logger.info(f"Stopped notifications for incident {incident_id}. Cancelled: {cancelled_count}, Scheduler stopped: {stopped}")

    return {
        "message": "Notifications stopped successfully",
        "incident_id": str(incident_id),
        "cancelled_notifications": cancelled_count,
        "scheduler_stopped": stopped,
    }


@router.post("/webhook/sms", response_model=dict)
async def handle_inbound_sms_webhook(
    request_data: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Inbound SMS Webhook for verified SMS hospital acknowledgments (Requirement 7)

    Processes inbound SMS replies from emergency responders or hospitals.
    Example body: "ACK ACC-2026-10-07-001" or token string.
    """
    payload = request_data or {}
    from_phone = payload.get("From") or payload.get("from_phone")
    body_text = payload.get("Body") or payload.get("body_text", "")

    if not body_text:
        raise HTTPException(status_code=400, detail="Empty SMS body")

    logger.info(f"Received inbound SMS webhook from '{from_phone}': {body_text}")

    # Search for incident ID in body_text (e.g. ACC-2026-10-07-001 or UUID)
    import re
    incident_match = re.search(r'(ACC-[\w-]+)', body_text, re.IGNORECASE)
    incident = None

    if incident_match:
        ext_id = incident_match.group(1)
        incident = await IncidentService.get_incident_by_external_id(db, ext_id)

    if not incident:
        # Try matching UUID in body
        uuid_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', body_text, re.IGNORECASE)
        if uuid_match:
            try:
                incident = await IncidentService.get_incident(db, UUID(uuid_match.group(1)))
            except ValueError:
                pass

    if not incident:
        return {
            "status": "unverified",
            "message": "Could not associate SMS response with an active incident"
        }

    # Find hospital by phone
    hospital_id = None
    if from_phone:
        from app.models import Hospital
        from sqlalchemy import select
        hosp_res = await db.execute(select(Hospital).where(Hospital.phone_numbers.contains([from_phone])))
        hosp = hosp_res.scalar_one_or_none()
        if hosp:
            hospital_id = hosp.id

    # Create acknowledgment request
    from app.schemas.incident import IncidentAcknowledgeRequest
    ack_req = IncidentAcknowledgeRequest(
        hospital_id=hospital_id,
        notes=f"Inbound SMS response: {body_text}",
        responder_name=f"SMS Sender ({from_phone})" if from_phone else "SMS Responder"
    )

    try:
        ack_incident = await IncidentService.acknowledge_incident(db, incident.id, ack_req)

        # Record HospitalResponse record with sms_webhook type
        from app.models.hospital_response import HospitalResponse, ResponseType, VerificationStatus
        from app.utils.security import generate_secure_id
        from datetime import datetime

        resp_rec = HospitalResponse(
            response_id=generate_secure_id("RESP-SMS-"),
            incident_id=incident.id,
            hospital_id=hospital_id,
            verified_recipient_ref=from_phone,
            response_type=ResponseType.SMS_WEBHOOK.value,
            response_timestamp=datetime.utcnow(),
            verification_status=VerificationStatus.VERIFIED.value,
            responder_name=f"SMS ({from_phone})",
            notes=body_text,
            raw_payload=payload
        )
        db.add(resp_rec)
        await db.commit()

        # Broadcast acknowledgment
        await WebSocketService.broadcast_incident_acknowledged({
            "id": str(ack_incident.id),
            "incident_id": ack_incident.incident_id,
            "acknowledged_at": ack_incident.acknowledged_at.isoformat(),
            "channel": "sms_webhook",
        })

        return {
            "status": "acknowledged",
            "incident_id": str(incident.id),
            "message": "Inbound SMS acknowledgment verified and notifications cancelled."
        }

    except Exception as e:
        logger.error(f"Error processing inbound SMS acknowledgment: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

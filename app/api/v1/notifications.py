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

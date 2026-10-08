"""
Incident Management API Routes
"""

from uuid import UUID
from typing import Optional, Union
from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentListResponse,
    IncidentAcknowledgeRequest,
    IncidentAcknowledgeResponse,
    IncidentResolveRequest,
    IncidentCancelRequest,
)
from app.models import IncidentStatus, SeverityLevel, User
from app.services.incident_service import IncidentService
from app.services.hospital_service import HospitalService
from app.services.scheduler_service import get_scheduler
from app.services.websocket_service import WebSocketService
from app.dependencies import get_current_user, get_operator_or_admin, check_maintenance_mode, get_optional_user
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new incident (AI Integration Endpoint)

    This endpoint is called by the AI detection module when an accident is detected.
    No authentication required for AI module integration.

    Idempotency: Use idempotency_key to prevent duplicate incident creation.
    """
    # Check maintenance mode
    if settings.MAINTENANCE_MODE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is in maintenance mode"
        )

    # Create incident
    incident = await IncidentService.create_incident(db, incident_data)

    # Broadcast incident creation
    await WebSocketService.broadcast_incident_created({
        "id": str(incident.id),
        "incident_id": incident.incident_id,
        "severity": incident.severity.value,
        "status": incident.status.value,
        "detected_at": incident.detected_at.isoformat(),
        "latitude": incident.latitude,
        "longitude": incident.longitude,
    })

    # If auto-notification is enabled and incident is eligible, schedule notification workflow
    if settings.AUTO_NOTIFICATION_ENABLED and incident.latitude and incident.longitude:
        # Schedule notifications
        scheduler = get_scheduler()
        background_tasks.add_task(
            scheduler.schedule_incident_notifications,
            incident.id
        )

        logger.info(f"Auto-notification scheduled for incident {incident.incident_id}")

    # --- NEW: Emergency Contact Notification (does NOT affect existing logic) ---
    # Runs in background so any failure never blocks the incident creation response
    background_tasks.add_task(
        _send_emergency_contact_notification,
        db,
        incident,
    )

    return incident


async def _send_emergency_contact_notification(db, incident) -> None:
    """
    Background task: send a single SMS to the configured emergency contact
    number if emergency_notifications_enabled is True.

    Rules:
    - Uses a per-incident deduplication: only fires once for each unique incident.id.
    - Does NOT modify the AI detection algorithm.
    - Does NOT notify hospitals.
    - Any exception is logged and swallowed so the main app is never crashed.
    """
    import asyncio
    from sqlalchemy import select
    from app.models.admin_setting import AdminSetting
    from app.services.notification_providers import NotificationProviderFactory
    from datetime import datetime

    # Simple in-process deduplication set (covers repeated calls within same process lifetime)
    if not hasattr(_send_emergency_contact_notification, "_sent_incident_ids"):
        _send_emergency_contact_notification._sent_incident_ids = set()  # type: ignore[attr-defined]

    incident_uuid = str(incident.id)
    if incident_uuid in _send_emergency_contact_notification._sent_incident_ids:  # type: ignore[attr-defined]
        logger.debug(f"Emergency contact notification already sent for incident {incident.incident_id} — skipping duplicate.")
        return

    try:
        # Use a new DB session-level read — db is already the request session passed from route
        res = await db.execute(select(AdminSetting).order_by(AdminSetting.created_at.desc()).limit(1))
        db_setting = res.scalar_one_or_none()

        if not db_setting or not db_setting.emergency_notifications_enabled:
            logger.debug(f"Emergency contact notifications OFF — skipping for incident {incident.incident_id}.")
            return

        contact_number = db_setting.emergency_contact_number
        if not contact_number:
            logger.warning(
                f"Emergency notifications enabled but no contact number configured. "
                f"Skipping for incident {incident.incident_id}."
            )
            return

        # Build emergency alert message
        severity_text = incident.severity.value.upper() if incident.severity else "UNKNOWN"
        location_text = incident.location_description or "Highway Segment"
        coords_str = (
            f"{incident.latitude:.5f}, {incident.longitude:.5f}"
            if incident.latitude and incident.longitude
            else "N/A"
        )
        detected_time = (
            incident.detected_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if incident.detected_at
            else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        message = (
            f"SafeWay Accident Alert: An accident has been detected.\n"
            f"ID: {incident.incident_id}\n"
            f"Severity: {severity_text}\n"
            f"Time: {detected_time}\n"
            f"Location: {location_text} (GPS: {coords_str})\n"
            f"Please dispatch emergency services immediately."
        )

        provider = NotificationProviderFactory.get_provider(channel="sms")
        result = await provider.send_sms(to_phone=contact_number, message=message)

        if result.success:
            _send_emergency_contact_notification._sent_incident_ids.add(incident_uuid)  # type: ignore[attr-defined]
            logger.info(
                f"Emergency contact notification sent to {contact_number} "
                f"for incident {incident.incident_id} via {result.provider_name}."
            )
        else:
            logger.warning(
                f"Emergency contact notification FAILED for incident {incident.incident_id}: "
                f"{result.error_message}"
            )

    except Exception as exc:
        # CRITICAL: must not crash the application
        logger.error(
            f"Emergency contact notification exception for incident {incident.incident_id}: {exc}",
            exc_info=True,
        )




@router.get("", response_model=IncidentListResponse)
async def get_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[IncidentStatus] = None,
    severity: Optional[SeverityLevel] = None,
    camera_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of incidents with optional filters
    """
    incidents, total = await IncidentService.get_incidents(
        db, skip, limit, status, severity, camera_id
    )

    return IncidentListResponse(
        incidents=incidents,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get incident details by ID
    """
    incident = await IncidentService.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    incident_data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
):
    """
    Update incident details

    Requires operator or admin role.
    """
    incident = await IncidentService.update_incident(db, incident_id, incident_data)

    # Broadcast incident update
    await WebSocketService.broadcast_incident_updated({
        "id": str(incident.id),
        "incident_id": incident.incident_id,
        "severity": incident.severity.value,
        "status": incident.status.value,
    })

    return incident


@router.post("/{incident_id}/acknowledge", response_model=IncidentAcknowledgeResponse)
async def acknowledge_incident(
    incident_id: str,
    acknowledge_data: IncidentAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Acknowledge an incident

    Can be called by:
    - Authenticated users (operators/admins)
    - Hospitals via secure acknowledgment token from notification
    """
    incident = await IncidentService.acknowledge_incident(db, incident_id, acknowledge_data)

    # Stop scheduled notifications
    scheduler = get_scheduler()
    await scheduler.stop_incident_notifications(incident.id)

    # Get hospital name if available
    hospital_name = None
    if incident.acknowledged_by_hospital_id:
        hospital = await HospitalService.get_hospital(db, incident.acknowledged_by_hospital_id)
        if hospital:
            hospital_name = hospital.name
            # Update hospital stats
            await HospitalService.update_hospital_response_stats(
                db, hospital.id, success=True
            )

    # Broadcast acknowledgment
    await WebSocketService.broadcast_incident_acknowledged({
        "id": str(incident.id),
        "incident_id": incident.incident_id,
        "acknowledged_at": incident.acknowledged_at.isoformat(),
        "hospital_name": hospital_name,
    })

    return IncidentAcknowledgeResponse(
        incident_id=incident.id,
        status=incident.status,
        acknowledged_at=incident.acknowledged_at,
        hospital_name=hospital_name,
        message="Incident acknowledged successfully. Emergency response en route."
    )


@router.get("/{incident_id}/acknowledge", response_model=IncidentAcknowledgeResponse)
async def acknowledge_incident_via_link(
    incident_id: str,
    token: str = Query(..., description="Secure acknowledgment token from emergency alert notification"),
    notes: Optional[str] = Query(None, description="Optional response notes"),
    responder_name: Optional[str] = Query(None, description="Responder name or title"),
    db: AsyncSession = Depends(get_db),
):
    """
    Acknowledge an incident via secure HTTP link (Requirement 7)
    """
    ack_req = IncidentAcknowledgeRequest(
        acknowledgment_token=token,
        notes=notes or "Acknowledged via link",
        responder_name=responder_name or "Emergency Responder"
    )
    return await acknowledge_incident(incident_id=incident_id, acknowledge_data=ack_req, db=db, current_user=None)


@router.get("/{incident_id}/images", response_model=list)
async def get_incident_images(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get accident images metadata for an incident (Requirement 9)
    """
    from app.services.image_service import ImageService
    images = await ImageService.get_images_for_incident(db, incident_id)
    return [
        {
            "id": str(img.id),
            "image_id": img.image_id,
            "incident_id": str(img.incident_id),
            "camera_id": str(img.camera_id) if img.camera_id else None,
            "capture_timestamp": img.capture_timestamp.isoformat() if img.capture_timestamp else None,
            "storage_reference": img.storage_reference,
            "file_type": img.file_type,
            "image_verification_status": img.image_verification_status,
        }
        for img in images
    ]


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: str,
    resolve_data: IncidentResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
):
    """
    Resolve an incident

    Requires operator or admin role.
    """
    incident = await IncidentService.resolve_incident(db, incident_id, resolve_data, current_user.id)

    # Stop any active notifications
    scheduler = get_scheduler()
    await scheduler.stop_incident_notifications(incident.id)

    # Broadcast resolution
    await WebSocketService.broadcast_incident_resolved({
        "id": str(incident.id),
        "incident_id": incident.incident_id,
        "resolved_at": incident.resolved_at.isoformat(),
        "resolved_by": str(incident.resolved_by),
    })

    return incident


@router.post("/{incident_id}/cancel", response_model=IncidentResponse)
async def cancel_incident(
    incident_id: str,
    cancel_data: IncidentCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
):
    """
    Cancel an incident (e.g., false positive)

    Requires operator or admin role.
    """
    incident = await IncidentService.cancel_incident(
        db, incident_id, cancel_data.reason, current_user.id
    )

    # Stop any active notifications
    scheduler = get_scheduler()
    await scheduler.stop_incident_notifications(incident.id)

    # Broadcast cancellation
    await WebSocketService.broadcast_incident_resolved({
        "id": str(incident.id),
        "incident_id": incident.incident_id,
        "status": incident.status.value,
        "cancelled": True,
        "reason": cancel_data.reason,
    })

    return incident

"""
Admin Control API Routes
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.schemas.admin import (
    SystemSettingsUpdate,
    SystemSettingsResponse,
    MaintenanceModeRequest,
    MaintenanceModeResponse,
    SystemHealthResponse,
    AuditLogResponse,
    AuditLogListResponse,
    EmergencyStopRequest,
    EmergencyStopResponse,
)
from app.models import User, Incident, IncidentStatus, Camera, CameraStatus
from app.services.scheduler_service import get_scheduler
from app.services.websocket_service import WebSocketService
from app.services.notification_service import NotificationService
from app.dependencies import get_admin_user
from app.config import settings
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Track application start time for uptime calculation
app_start_time = time.time()


@router.patch("/settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_data: SystemSettingsUpdate,
    current_user: User = Depends(get_admin_user),
):
    """
    Update system settings

    Requires admin role.
    """
    # Update settings (in production, store in database)
    if settings_data.auto_notification_enabled is not None:
        settings.AUTO_NOTIFICATION_ENABLED = settings_data.auto_notification_enabled

    if settings_data.notification_interval_seconds is not None:
        settings.NOTIFICATION_INTERVAL_SECONDS = settings_data.notification_interval_seconds

    if settings_data.hospital_search_radius_km is not None:
        settings.HOSPITAL_SEARCH_RADIUS_KM = settings_data.hospital_search_radius_km

    if settings_data.max_hospitals_to_notify is not None:
        settings.MAX_HOSPITALS_TO_NOTIFY = settings_data.max_hospitals_to_notify

    if settings_data.max_notification_retries is not None:
        settings.MAX_NOTIFICATION_RETRIES = settings_data.max_notification_retries

    if settings_data.test_mode is not None:
        settings.TEST_MODE = settings_data.test_mode

    logger.info(f"System settings updated by {current_user.username}")

    return SystemSettingsResponse(
        auto_notification_enabled=settings.AUTO_NOTIFICATION_ENABLED,
        notification_interval_seconds=settings.NOTIFICATION_INTERVAL_SECONDS,
        hospital_search_radius_km=settings.HOSPITAL_SEARCH_RADIUS_KM,
        max_hospitals_to_notify=settings.MAX_HOSPITALS_TO_NOTIFY,
        max_notification_retries=settings.MAX_NOTIFICATION_RETRIES,
        maintenance_mode=settings.MAINTENANCE_MODE,
        test_mode=settings.TEST_MODE,
        updated_at=datetime.utcnow(),
    )


@router.post("/maintenance", response_model=MaintenanceModeResponse)
async def toggle_maintenance_mode(
    maintenance_data: MaintenanceModeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Enable or disable maintenance mode

    Requires admin role.

    When enabled:
    - All camera monitoring stops
    - No new incidents are processed
    - Notification scheduling is paused
    - Only health checks and admin endpoints remain active
    """
    settings.MAINTENANCE_MODE = maintenance_data.enabled

    if maintenance_data.enabled:
        # Stop all scheduled notifications
        scheduler = get_scheduler()
        stopped_count = await scheduler.stop_all_notifications()

        logger.warning(f"Maintenance mode ENABLED by {current_user.username}. Stopped {stopped_count} notification jobs.")
        message = f"Maintenance mode enabled. {stopped_count} notification jobs stopped."
    else:
        logger.info(f"Maintenance mode DISABLED by {current_user.username}")
        message = "Maintenance mode disabled. System restored to normal operation."

    # Broadcast maintenance mode change
    await WebSocketService.broadcast_maintenance_mode_changed(
        enabled=maintenance_data.enabled,
        reason=maintenance_data.reason
    )

    return MaintenanceModeResponse(
        maintenance_mode=settings.MAINTENANCE_MODE,
        reason=maintenance_data.reason,
        started_at=datetime.utcnow() if maintenance_data.enabled else None,
        scheduled_end_time=maintenance_data.scheduled_end_time,
        message=message,
    )


@router.post("/notifications/stop-all", response_model=EmergencyStopResponse)
async def emergency_stop_all_notifications(
    stop_data: EmergencyStopRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    EMERGENCY STOP: Stop all active notifications immediately

    Requires admin role.

    This will:
    - Cancel all scheduled notification jobs
    - Mark all pending notifications as cancelled
    - Stop notifications for all active incidents
    """
    scheduler = get_scheduler()

    # Stop all scheduled jobs
    scheduler_stopped_count = await scheduler.stop_all_notifications()

    # Get all active incidents
    result = await db.execute(
        select(Incident).where(
            Incident.status.in_([
                IncidentStatus.ACTIVE,
                IncidentStatus.NOTIFICATION_PENDING,
                IncidentStatus.NOTIFIED
            ])
        )
    )
    active_incidents = result.scalars().all()

    affected_incident_ids = []
    total_cancelled = 0

    for incident in active_incidents:
        # Cancel notifications for each incident
        cancelled = await NotificationService.cancel_notifications_for_incident(db, incident.id)
        total_cancelled += cancelled
        affected_incident_ids.append(incident.id)

        # Update incident
        incident.notification_stopped_at = datetime.utcnow()

    await db.commit()

    # Broadcast emergency stop
    await WebSocketService.broadcast_system_alert(
        alert_type="emergency_stop",
        message_text=f"All notifications stopped by admin. Reason: {stop_data.reason}"
    )

    logger.critical(
        f"EMERGENCY STOP executed by {current_user.username}. "
        f"Scheduler jobs stopped: {scheduler_stopped_count}, "
        f"Notifications cancelled: {total_cancelled}, "
        f"Incidents affected: {len(affected_incident_ids)}"
    )

    return EmergencyStopResponse(
        stopped_count=scheduler_stopped_count + total_cancelled,
        incidents_affected=affected_incident_ids,
        timestamp=datetime.utcnow(),
        message=f"Emergency stop executed successfully. {len(affected_incident_ids)} incidents affected.",
    )


@router.get("/health", response_model=SystemHealthResponse)
async def system_health_check(
    db: AsyncSession = Depends(get_db),
):
    """
    System health check

    No authentication required for monitoring purposes.
    """
    # Check database connection
    try:
        await db.execute(select(1))
        database_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        database_connected = False

    # Get scheduler status
    scheduler = get_scheduler()
    scheduler_running = scheduler.is_running()

    # Get active incidents count
    result = await db.execute(
        select(func.count()).select_from(Incident).where(
            Incident.status.in_([
                IncidentStatus.ACTIVE,
                IncidentStatus.NOTIFICATION_PENDING,
                IncidentStatus.NOTIFIED
            ])
        )
    )
    active_incidents = result.scalar()

    # Get online cameras count
    result = await db.execute(
        select(func.count()).select_from(Camera).where(
            Camera.status.in_([CameraStatus.ONLINE, CameraStatus.MONITORING])
        )
    )
    online_cameras = result.scalar()

    # Get pending notifications count (would need to query Notification table)
    pending_notifications = 0  # Simplified

    # Calculate uptime
    uptime_seconds = time.time() - app_start_time

    # Determine overall status
    if database_connected and scheduler_running:
        overall_status = "healthy"
    elif database_connected:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return SystemHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        database_connected=database_connected,
        scheduler_running=scheduler_running,
        active_incidents=active_incidents,
        pending_notifications=pending_notifications,
        online_cameras=online_cameras,
        maintenance_mode=settings.MAINTENANCE_MODE,
        uptime_seconds=uptime_seconds,
    )


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get audit logs

    Requires admin role.
    """
    # Simplified audit log retrieval
    # In production, implement full audit log querying from AuditLog model

    return AuditLogListResponse(
        logs=[],
        total=0,
        page=skip // limit + 1,
        page_size=limit,
    )

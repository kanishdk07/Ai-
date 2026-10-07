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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Update system settings (Requirement 3 & 10)

    Requires admin role.
    """
    from app.models.admin_setting import AdminSetting
    from app.models.audit_log import AuditLog

    # Update in-memory settings
    if settings_data.auto_notification_enabled is not None:
        settings.AUTO_NOTIFICATION_ENABLED = settings_data.auto_notification_enabled

    if settings_data.notification_interval_seconds is not None:
        # Clamp interval between 30s and 300s (Requirement 6)
        interval = max(30, min(300, settings_data.notification_interval_seconds))
        settings.NOTIFICATION_INTERVAL_SECONDS = interval

    if settings_data.hospital_search_radius_km is not None:
        settings.HOSPITAL_SEARCH_RADIUS_KM = settings_data.hospital_search_radius_km

    if settings_data.max_hospitals_to_notify is not None:
        settings.MAX_HOSPITALS_TO_NOTIFY = settings_data.max_hospitals_to_notify

    if settings_data.max_notification_retries is not None:
        settings.MAX_NOTIFICATION_RETRIES = settings_data.max_notification_retries

    if settings_data.test_mode is not None:
        settings.TEST_MODE = settings_data.test_mode

    # DB Persistence in admin_settings table
    res = await db.execute(select(AdminSetting).order_by(AdminSetting.created_at.desc()).limit(1))
    db_setting = res.scalar_one_or_none()
    if not db_setting:
        db_setting = AdminSetting(system_configuration_version=1)
        db.add(db_setting)

    db_setting.auto_notification_enabled = settings.AUTO_NOTIFICATION_ENABLED
    db_setting.notification_repeat_interval = settings.NOTIFICATION_INTERVAL_SECONDS
    db_setting.default_hospital_search_radius = settings.HOSPITAL_SEARCH_RADIUS_KM
    db_setting.maintenance_mode = settings.MAINTENANCE_MODE
    db_setting.last_updated_by = current_user.id
    db_setting.system_configuration_version += 1

    # Record Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE_SETTINGS",
        resource_type="admin_setting",
        resource_id=str(db_setting.id),
        description=f"System settings updated by {current_user.username}"
    )
    db.add(audit)

    await db.commit()
    await db.refresh(db_setting)

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
    Enable or disable maintenance mode (Requirement 3 & 10)

    Requires admin role.
    """
    from app.models.admin_setting import AdminSetting
    from app.models.audit_log import AuditLog

    settings.MAINTENANCE_MODE = maintenance_data.enabled

    # Persist in DB
    res = await db.execute(select(AdminSetting).order_by(AdminSetting.created_at.desc()).limit(1))
    db_setting = res.scalar_one_or_none()
    if not db_setting:
        db_setting = AdminSetting(system_configuration_version=1)
        db.add(db_setting)

    db_setting.maintenance_mode = maintenance_data.enabled
    db_setting.last_updated_by = current_user.id

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="TOGGLE_MAINTENANCE_MODE",
        resource_type="admin_setting",
        description=f"Maintenance mode set to {maintenance_data.enabled}. Reason: {maintenance_data.reason}"
    )
    db.add(audit)

    if maintenance_data.enabled:
        scheduler = get_scheduler()
        stopped_count = await scheduler.stop_all_notifications()
        logger.warning(f"Maintenance mode ENABLED by {current_user.username}. Stopped {stopped_count} notification jobs.")
        message = f"Maintenance mode enabled. {stopped_count} notification jobs stopped."
    else:
        logger.info(f"Maintenance mode DISABLED by {current_user.username}")
        message = "Maintenance mode disabled. System restored to normal operation."

    await db.commit()

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
    """
    from app.models.audit_log import AuditLog

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
        cancelled = await NotificationService.cancel_notifications_for_incident(db, incident.id)
        total_cancelled += cancelled
        affected_incident_ids.append(incident.id)
        incident.notification_stopped_at = datetime.utcnow()

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="EMERGENCY_STOP_ALL",
        resource_type="notifications",
        description=f"Emergency stop all notifications executed. Reason: {stop_data.reason}"
    )
    db.add(audit)

    await db.commit()

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
    """
    try:
        await db.execute(select(1))
        database_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        database_connected = False

    scheduler = get_scheduler()
    scheduler_running = scheduler.is_running()

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

    result = await db.execute(
        select(func.count()).select_from(Camera).where(
            Camera.status.in_([CameraStatus.ONLINE, CameraStatus.MONITORING])
        )
    )
    online_cameras = result.scalar()

    from app.models import Notification, NotificationStatus
    res_notif = await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.status == NotificationStatus.PENDING
        )
    )
    pending_notifications = res_notif.scalar() or 0

    uptime_seconds = time.time() - app_start_time

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
    Get audit logs (Requirement 10)

    Requires admin role.
    """
    from app.models.audit_log import AuditLog
    from sqlalchemy import and_

    query = select(AuditLog)
    filters = []

    if action:
        filters.append(AuditLog.action == action)
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)

    if filters:
        query = query.where(and_(*filters))

    # Total count
    count_query = select(func.count()).select_from(AuditLog)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Paginated results
    query = query.offset(skip).limit(limit).order_by(AuditLog.created_at.desc())
    logs_res = await db.execute(query)
    logs = logs_res.scalars().all()

    log_responses = [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=log.username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            description=log.description,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return AuditLogListResponse(
        logs=log_responses,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )

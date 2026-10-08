"""
Camera Management API Routes
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraActionRequest,
)
from app.models import CameraType, CameraStatus, User
from app.services.camera_service import CameraService
from app.services.websocket_service import WebSocketService
from app.dependencies import get_operator_or_admin, check_maintenance_mode

router = APIRouter()


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
    _: None = Depends(check_maintenance_mode),
):
    """
    Register a new camera

    Requires operator or admin role.
    """
    camera = await CameraService.create_camera(db, camera_data, current_user.id)

    # Broadcast camera creation
    await WebSocketService.broadcast_camera_status_changed({
        "camera_id": camera.camera_id,
        "status": camera.status.value,
        "action": "created",
    })

    return camera


@router.get("", response_model=CameraListResponse)
async def get_cameras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    camera_type: Optional[CameraType] = None,
    status: Optional[CameraStatus] = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_maintenance_mode),
):
    """
    Get list of cameras with optional filters
    """
    cameras, total = await CameraService.get_cameras(db, skip, limit, camera_type, status)

    return CameraListResponse(
        cameras=cameras,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_maintenance_mode),
):
    """
    Get camera details by ID
    """
    camera = await CameraService.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    return camera


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
    _: None = Depends(check_maintenance_mode),
):
    """
    Update camera details

    Requires operator or admin role.
    """
    camera = await CameraService.update_camera(db, camera_id, camera_data)

    # Broadcast camera update
    await WebSocketService.broadcast_camera_status_changed({
        "camera_id": camera.camera_id,
        "status": camera.status.value,
        "action": "updated",
    })

    return camera


@router.post("/{camera_id}/start", response_model=CameraResponse)
async def start_camera_monitoring(
    camera_id: str,
    action_data: CameraActionRequest = CameraActionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
    _: None = Depends(check_maintenance_mode),
):
    """
    Start camera monitoring

    Requires operator or admin role.
    """
    camera = await CameraService.start_monitoring(db, camera_id)

    # Broadcast camera status change
    await WebSocketService.broadcast_camera_status_changed({
        "camera_id": camera.camera_id,
        "status": camera.status.value,
        "action": "monitoring_started",
        "reason": action_data.reason,
    })

    return camera


@router.post("/{camera_id}/stop", response_model=CameraResponse)
async def stop_camera_monitoring(
    camera_id: str,
    action_data: CameraActionRequest = CameraActionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
    _: None = Depends(check_maintenance_mode),
):
    """
    Stop camera monitoring

    Requires operator or admin role.
    """
    camera = await CameraService.stop_monitoring(db, camera_id)

    # Broadcast camera status change
    await WebSocketService.broadcast_camera_status_changed({
        "camera_id": camera.camera_id,
        "status": camera.status.value,
        "action": "monitoring_stopped",
        "reason": action_data.reason,
    })

    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
    _: None = Depends(check_maintenance_mode),
):
    """
    Delete a camera

    Requires operator or admin role.
    """
    await CameraService.delete_camera(db, camera_id)

    # Broadcast camera deletion
    await WebSocketService.broadcast_camera_status_changed({
        "camera_id": str(camera_id),
        "action": "deleted",
    })

    return None

"""
Camera Service
Handles camera management operations
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.sql import func
from fastapi import HTTPException, status
# GeoAlchemy2 available for PostgreSQL; lat/lon used directly for SQLite
from app.models import Camera, CameraStatus, CameraType
from app.schemas.camera import CameraCreate, CameraUpdate
from app.utils.security import encrypt_camera_credentials, decrypt_camera_credentials
import logging

logger = logging.getLogger(__name__)


class CameraService:
    """Service for camera operations"""

    @staticmethod
    async def create_camera(db: AsyncSession, camera_data: CameraCreate, user_id: UUID) -> Camera:
        """
        Create a new camera

        Args:
            db: Database session
            camera_data: Camera creation data
            user_id: ID of user creating the camera

        Returns:
            Created camera

        Raises:
            HTTPException: If camera_id already exists
        """
        # Check if camera_id already exists
        result = await db.execute(
            select(Camera).where(Camera.camera_id == camera_data.camera_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Camera with ID {camera_data.camera_id} already exists"
            )

        # Encrypt connection config if present
        connection_config = None
        if camera_data.connection_config:
            connection_config = encrypt_camera_credentials(camera_data.connection_config)

        # Create camera
        new_camera = Camera(
            camera_id=camera_data.camera_id,
            name=camera_data.name,
            camera_type=camera_data.camera_type,
            location_name=camera_data.location_name,
            latitude=camera_data.latitude,
            longitude=camera_data.longitude,
            connection_config=connection_config,
            description=camera_data.description,
            meta_data=camera_data.metadata,
            created_by=user_id,
        )

        # (PostGIS location column removed for SQLite compatibility; lat/lon stored as Float)

        db.add(new_camera)
        await db.commit()
        await db.refresh(new_camera)

        logger.info(f"Camera created: {new_camera.camera_id}")
        return new_camera

    @staticmethod
    async def get_camera(db: AsyncSession, camera_id: str) -> Optional[Camera]:
        """Get camera by string ID"""
        result = await db.execute(select(Camera).where(Camera.id == str(camera_id)))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_camera_by_external_id(db: AsyncSession, camera_id: str) -> Optional[Camera]:
        """Get camera by external camera_id"""
        result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_cameras(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        camera_type: Optional[CameraType] = None,
        status: Optional[CameraStatus] = None,
    ) -> tuple[List[Camera], int]:
        """
        Get list of cameras with pagination and filters

        Returns:
            Tuple of (cameras list, total count)
        """
        query = select(Camera)

        # Apply filters
        filters = []
        if camera_type:
            filters.append(Camera.camera_type == camera_type)
        if status:
            filters.append(Camera.status == status)

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count()).select_from(Camera)
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Camera.created_at.desc())
        result = await db.execute(query)
        cameras = result.scalars().all()

        return list(cameras), total

    @staticmethod
    async def update_camera(
        db: AsyncSession,
        camera_id: UUID,
        camera_data: CameraUpdate
    ) -> Camera:
        """Update camera"""
        camera = await CameraService.get_camera(db, camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )

        # Update fields
        update_data = camera_data.model_dump(exclude_unset=True)

        # Handle connection config encryption
        if "connection_config" in update_data and update_data["connection_config"]:
            update_data["connection_config"] = encrypt_camera_credentials(
                update_data["connection_config"]
            )

        # Update location if coordinates changed
        if "latitude" in update_data and "longitude" in update_data:
            camera.location = func.ST_SetSRID(
                func.ST_MakePoint(update_data["longitude"], update_data["latitude"]),
                4326
            )

        for key, value in update_data.items():
            setattr(camera, key, value)

        await db.commit()
        await db.refresh(camera)

        logger.info(f"Camera updated: {camera.camera_id}")
        return camera

    @staticmethod
    async def start_monitoring(db: AsyncSession, camera_id: UUID) -> Camera:
        """Start camera monitoring"""
        camera = await CameraService.get_camera(db, camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )

        if not camera.can_monitor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Camera is not in a state to start monitoring"
            )

        camera.is_monitoring = True
        camera.status = CameraStatus.MONITORING
        camera.last_active_at = func.now()

        await db.commit()
        await db.refresh(camera)

        logger.info(f"Camera monitoring started: {camera.camera_id}")
        return camera

    @staticmethod
    async def stop_monitoring(db: AsyncSession, camera_id: UUID) -> Camera:
        """Stop camera monitoring"""
        camera = await CameraService.get_camera(db, camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )

        camera.is_monitoring = False
        camera.status = CameraStatus.ONLINE

        await db.commit()
        await db.refresh(camera)

        logger.info(f"Camera monitoring stopped: {camera.camera_id}")
        return camera

    @staticmethod
    async def delete_camera(db: AsyncSession, camera_id: UUID) -> bool:
        """Delete camera"""
        camera = await CameraService.get_camera(db, camera_id)
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )

        await db.delete(camera)
        await db.commit()

        logger.info(f"Camera deleted: {camera.camera_id}")
        return True

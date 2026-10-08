"""
Image Service
Handles accident image metadata registration, storage reference tracking, and secure serving
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from app.models.accident_image import AccidentImage, ImageVerificationStatus
from app.utils.security import generate_secure_id
from app.config import settings
import os
import logging

logger = logging.getLogger(__name__)


class ImageService:
    """Service for managing accident image metadata and storage references"""

    @staticmethod
    async def create_image_metadata(
        db: AsyncSession,
        storage_reference: str,
        incident_id: Optional[UUID] = None,
        camera_id: Optional[UUID] = None,
        file_type: str = "image/jpeg",
        file_size_bytes: Optional[int] = None,
        verification_status: str = ImageVerificationStatus.PENDING.value,
        meta_data: Optional[dict] = None
    ) -> AccidentImage:
        """
        Create image metadata record (Requirement 9)

        Args:
            db: Database session
            storage_reference: File path or storage key (no binary stored in DB)
            incident_id: Associated incident UUID
            camera_id: Associated camera UUID
            file_type: MIME type
            file_size_bytes: Size in bytes
            verification_status: Verification state
            meta_data: Extra JSON metadata

        Returns:
            Created AccidentImage record
        """
        image_id = generate_secure_id("IMG-")

        new_image = AccidentImage(
            image_id=image_id,
            incident_id=incident_id,
            camera_id=camera_id,
            storage_reference=storage_reference,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            image_verification_status=verification_status,
            meta_data=meta_data or {}
        )

        db.add(new_image)
        await db.commit()
        await db.refresh(new_image)

        logger.info(f"Accident image metadata created: {new_image.image_id} for incident {incident_id}")
        return new_image

    @staticmethod
    async def get_image_by_id(db: AsyncSession, image_id: str) -> Optional[AccidentImage]:
        """Get image metadata by image_id string or UUID"""
        result = await db.execute(select(AccidentImage).where(AccidentImage.image_id == image_id))
        img = result.scalar_one_or_none()
        if not img:
            try:
                uuid_obj = UUID(image_id)
                result = await db.execute(select(AccidentImage).where(AccidentImage.id == uuid_obj))
                img = result.scalar_one_or_none()
            except ValueError:
                pass
        return img

    @staticmethod
    async def get_images_for_incident(db: AsyncSession, incident_id: UUID) -> List[AccidentImage]:
        """Get all image metadata records for an incident"""
        result = await db.execute(
            select(AccidentImage)
            .where(AccidentImage.incident_id == incident_id)
            .order_by(AccidentImage.capture_timestamp.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def verify_image(
        db: AsyncSession,
        image_id: str,
        verification_status: ImageVerificationStatus
    ) -> AccidentImage:
        """Update image verification status"""
        img = await ImageService.get_image_by_id(db, image_id)
        if not img:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Accident image not found"
            )

        img.image_verification_status = verification_status.value
        await db.commit()
        await db.refresh(img)
        return img

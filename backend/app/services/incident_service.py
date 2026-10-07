"""
Incident Service
Handles incident creation, management, and lifecycle
"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
from app.models import Incident, IncidentStatus, SeverityLevel, Camera
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentAcknowledgeRequest,
    IncidentResolveRequest,
)
from app.utils.validators import validate_incident_id
from app.utils.security import generate_secure_id, verify_acknowledgment_token
import logging

logger = logging.getLogger(__name__)


class IncidentService:
    """Service for incident operations"""

    @staticmethod
    async def create_incident(db: AsyncSession, incident_data: IncidentCreate) -> Incident:
        """
        Create a new incident from AI detection

        Args:
            db: Database session
            incident_data: Incident creation data

        Returns:
            Created incident

        Raises:
            HTTPException: If incident_id is invalid or duplicate
        """
        # Validate incident ID format
        if not validate_incident_id(incident_data.incident_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid incident_id format"
            )

        # Check for duplicate incident_id
        result = await db.execute(
            select(Incident).where(Incident.incident_id == incident_data.incident_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Incident with ID {incident_data.incident_id} already exists"
            )

        # Check idempotency key if provided
        if incident_data.idempotency_key:
            result = await db.execute(
                select(Incident).where(Incident.idempotency_key == incident_data.idempotency_key)
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.info(f"Idempotent request detected, returning existing incident: {existing.incident_id}")
                return existing

        # Find camera by external ID if provided
        camera_id = None
        if incident_data.camera_external_id:
            camera_result = await db.execute(
                select(Camera).where(Camera.camera_id == incident_data.camera_external_id)
            )
            camera = camera_result.scalar_one_or_none()
            if camera:
                camera_id = camera.id
                # Update camera detection stats
                camera.last_detection_at = func.now()
                camera.total_detections += 1

        # Create incident
        new_incident = Incident(
            incident_id=incident_data.incident_id,
            camera_id=camera_id,
            camera_external_id=incident_data.camera_external_id,
            detected_at=incident_data.detected_at,
            accident_detected=incident_data.accident_detected,
            severity=incident_data.severity,
            confidence_score=incident_data.confidence_score,
            latitude=incident_data.latitude,
            longitude=incident_data.longitude,
            location_description=incident_data.location_description,
            accident_image_url=incident_data.accident_image_url,
            vehicle_count=incident_data.vehicle_count,
            vehicle_info=incident_data.vehicle_info,
            ai_event_data=incident_data.ai_event_data,
            idempotency_key=incident_data.idempotency_key,
            status=IncidentStatus.DETECTED,
        )

        # Set PostGIS location if coordinates provided
        if incident_data.latitude and incident_data.longitude:
            new_incident.location = func.ST_SetSRID(
                func.ST_MakePoint(incident_data.longitude, incident_data.latitude),
                4326
            )

        db.add(new_incident)
        await db.commit()
        await db.refresh(new_incident)

        logger.info(f"Incident created: {new_incident.incident_id} - Severity: {new_incident.severity}")
        return new_incident

    @staticmethod
    async def get_incident(db: AsyncSession, incident_id: UUID) -> Optional[Incident]:
        """Get incident by UUID"""
        result = await db.execute(select(Incident).where(Incident.id == incident_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_incident_by_external_id(db: AsyncSession, incident_id: str) -> Optional[Incident]:
        """Get incident by external incident_id"""
        result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_incidents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[IncidentStatus] = None,
        severity: Optional[SeverityLevel] = None,
        camera_id: Optional[UUID] = None,
    ) -> Tuple[List[Incident], int]:
        """Get list of incidents with pagination and filters"""
        query = select(Incident)

        # Apply filters
        filters = []
        if status:
            filters.append(Incident.status == status)
        if severity:
            filters.append(Incident.severity == severity)
        if camera_id:
            filters.append(Incident.camera_id == camera_id)

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count()).select_from(Incident)
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Incident.detected_at.desc())
        result = await db.execute(query)
        incidents = result.scalars().all()

        return list(incidents), total

    @staticmethod
    async def get_active_incidents(db: AsyncSession) -> List[Incident]:
        """Get all active incidents that can trigger notifications"""
        result = await db.execute(
            select(Incident).where(
                Incident.status.in_([
                    IncidentStatus.ACTIVE,
                    IncidentStatus.NOTIFICATION_PENDING,
                    IncidentStatus.NOTIFIED
                ])
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_incident(
        db: AsyncSession,
        incident_id: UUID,
        incident_data: IncidentUpdate
    ) -> Incident:
        """Update incident"""
        incident = await IncidentService.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        # Update fields
        update_data = incident_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(incident, key, value)

        await db.commit()
        await db.refresh(incident)

        logger.info(f"Incident updated: {incident.incident_id}")
        return incident

    @staticmethod
    async def acknowledge_incident(
        db: AsyncSession,
        incident_id: UUID,
        acknowledge_data: IncidentAcknowledgeRequest
    ) -> Incident:
        """
        Acknowledge an incident from hospital

        Args:
            db: Database session
            incident_id: Incident UUID
            acknowledge_data: Acknowledgment data

        Returns:
            Updated incident

        Raises:
            HTTPException: If incident not found or already acknowledged
        """
        incident = await IncidentService.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        if incident.status == IncidentStatus.ACKNOWLEDGED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incident already acknowledged"
            )

        if not incident.can_notify:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incident is not in a state that can be acknowledged"
            )

        # Verify acknowledgment token if provided
        if acknowledge_data.acknowledgment_token:
            token_data = verify_acknowledgment_token(acknowledge_data.acknowledgment_token)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid acknowledgment token"
                )
            # Use hospital_id from token
            acknowledge_data.hospital_id = UUID(token_data["hospital_id"])

        # Update incident
        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.acknowledged_at = datetime.utcnow()
        incident.acknowledged_by_hospital_id = acknowledge_data.hospital_id
        incident.acknowledgment_details = {
            "notes": acknowledge_data.notes,
            "responder_name": acknowledge_data.responder_name,
        }
        incident.notification_stopped_at = datetime.utcnow()

        await db.commit()
        await db.refresh(incident)

        logger.info(f"Incident acknowledged: {incident.incident_id}")
        return incident

    @staticmethod
    async def resolve_incident(
        db: AsyncSession,
        incident_id: UUID,
        resolve_data: IncidentResolveRequest,
        user_id: UUID
    ) -> Incident:
        """Resolve an incident"""
        incident = await IncidentService.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        if incident.status == IncidentStatus.RESOLVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incident already resolved"
            )

        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
        incident.resolved_by = user_id
        incident.resolution_notes = resolve_data.resolution_notes

        if incident.notification_stopped_at is None:
            incident.notification_stopped_at = datetime.utcnow()

        await db.commit()
        await db.refresh(incident)

        logger.info(f"Incident resolved: {incident.incident_id}")
        return incident

    @staticmethod
    async def cancel_incident(
        db: AsyncSession,
        incident_id: UUID,
        reason: str,
        user_id: UUID
    ) -> Incident:
        """Cancel an incident"""
        incident = await IncidentService.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        if incident.is_closed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incident already closed"
            )

        incident.status = IncidentStatus.CANCELLED
        incident.resolved_at = datetime.utcnow()
        incident.resolved_by = user_id
        incident.resolution_notes = f"Cancelled: {reason}"

        if incident.notification_stopped_at is None:
            incident.notification_stopped_at = datetime.utcnow()

        await db.commit()
        await db.refresh(incident)

        logger.info(f"Incident cancelled: {incident.incident_id}")
        return incident

    @staticmethod
    async def activate_incident(db: AsyncSession, incident_id: UUID) -> Incident:
        """Move incident to active status for notification"""
        incident = await IncidentService.get_incident(db, incident_id)
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )

        incident.status = IncidentStatus.ACTIVE
        await db.commit()
        await db.refresh(incident)

        logger.info(f"Incident activated: {incident.incident_id}")
        return incident

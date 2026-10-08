"""
Hospital Service
Handles hospital management and nearby search operations
"""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from fastapi import HTTPException, status
from geoalchemy2.functions import ST_Distance, ST_SetSRID, ST_MakePoint
from geoalchemy2 import Geography
from app.models import Hospital
from app.schemas.hospital import HospitalCreate, HospitalUpdate
from app.config import settings
from app.services.google_maps_service import GoogleMapsService
import logging

logger = logging.getLogger(__name__)


class HospitalService:
    """Service for hospital operations"""

    @staticmethod
    async def create_hospital(db: AsyncSession, hospital_data: HospitalCreate) -> Hospital:
        """
        Create a new hospital

        Args:
            db: Database session
            hospital_data: Hospital creation data

        Returns:
            Created hospital
        """
        # Create hospital
        new_hospital = Hospital(
            name=hospital_data.name,
            hospital_code=hospital_data.hospital_code,
            phone_numbers=hospital_data.phone_numbers,
            email=hospital_data.email,
            emergency_contact=hospital_data.emergency_contact,
            address=hospital_data.address,
            city=hospital_data.city,
            state=hospital_data.state,
            postal_code=hospital_data.postal_code,
            latitude=hospital_data.latitude,
            longitude=hospital_data.longitude,
            has_emergency_dept=hospital_data.has_emergency_dept,
            has_trauma_center=hospital_data.has_trauma_center,
            has_ambulance=hospital_data.has_ambulance,
            bed_capacity=hospital_data.bed_capacity,
            is_24_7=hospital_data.is_24_7,
            accepts_sms=hospital_data.accepts_sms,
            accepts_email=hospital_data.accepts_email,
            accepts_call=hospital_data.accepts_call,
            description=hospital_data.description,
            website=hospital_data.website,
            metadata=hospital_data.metadata,
        )

        # Set PostGIS location
        new_hospital.location = func.ST_SetSRID(
            func.ST_MakePoint(hospital_data.longitude, hospital_data.latitude),
            4326
        )

        db.add(new_hospital)
        await db.commit()
        await db.refresh(new_hospital)

        logger.info(f"Hospital created: {new_hospital.name}")
        return new_hospital

    @staticmethod
    async def get_hospital(db: AsyncSession, hospital_id: UUID) -> Optional[Hospital]:
        """Get hospital by ID"""
        result = await db.execute(select(Hospital).where(Hospital.id == hospital_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_hospitals(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Hospital], int]:
        """Get list of hospitals with pagination"""
        query = select(Hospital)

        if is_active is not None:
            query = query.where(Hospital.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(Hospital)
        if is_active is not None:
            count_query = count_query.where(Hospital.is_active == is_active)
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Hospital.name)
        result = await db.execute(query)
        hospitals = result.scalars().all()

        return list(hospitals), total

    @staticmethod
    async def find_nearby_hospitals(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: Optional[float] = None,
        limit: int = 10,
    ) -> List[dict]:
        """
        Find hospitals near a location

        Args:
            db: Database session
            latitude: Location latitude
            longitude: Location longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of results

        Returns:
            List of hospitals with distance
        """
        if radius_km is None:
            radius_km = settings.HOSPITAL_SEARCH_RADIUS_KM

        # Create point for the incident location
        incident_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

        # Calculate distance in meters and filter by radius
        distance_m = func.ST_Distance(
            Hospital.location.cast(Geography),
            incident_point.cast(Geography)
        )

        query = (
            select(
                Hospital,
                (distance_m / 1000).label('distance_km')  # Convert to kilometers
            )
            .where(
                and_(
                    Hospital.is_active == True,
                    Hospital.is_available == True,
                    distance_m <= radius_km * 1000  # Convert km to meters
                )
            )
            .order_by(distance_m)
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        nearby_hospitals = []
        for hospital, distance in rows:
            directions_url = GoogleMapsService.get_directions_url(
                origin_lat=latitude,
                origin_lng=longitude,
                destination_lat=hospital.latitude,
                destination_lng=hospital.longitude,
            )
            embed_url = GoogleMapsService.get_embed_map_url(
                latitude=hospital.latitude,
                longitude=hospital.longitude,
            )
            static_map_url = GoogleMapsService.get_static_map_url(
                latitude=hospital.latitude,
                longitude=hospital.longitude,
            )

            hospital_dict = {
                **hospital.__dict__,
                'distance_km': round(distance, 2),
                'google_maps_directions_url': directions_url,
                'google_maps_embed_url': embed_url,
                'google_maps_static_map_url': static_map_url,
                'road_distance_km': None,
                'road_duration_minutes': None,
            }
            # Remove SQLAlchemy internal state
            hospital_dict.pop('_sa_instance_state', None)
            nearby_hospitals.append(hospital_dict)

        logger.info(f"Found {len(nearby_hospitals)} hospitals within {radius_km}km")
        return nearby_hospitals

    @staticmethod
    async def update_hospital(
        db: AsyncSession,
        hospital_id: UUID,
        hospital_data: HospitalUpdate
    ) -> Hospital:
        """Update hospital"""
        hospital = await HospitalService.get_hospital(db, hospital_id)
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital not found"
            )

        # Update fields
        update_data = hospital_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(hospital, key, value)

        await db.commit()
        await db.refresh(hospital)

        logger.info(f"Hospital updated: {hospital.name}")
        return hospital

    @staticmethod
    async def update_hospital_response_stats(
        db: AsyncSession,
        hospital_id: UUID,
        success: bool
    ) -> Hospital:
        """Update hospital response statistics"""
        hospital = await HospitalService.get_hospital(db, hospital_id)
        if not hospital:
            return None

        hospital.total_responses += 1
        if success:
            hospital.successful_responses += 1
        hospital.last_notified_at = func.now()

        await db.commit()
        await db.refresh(hospital)

        return hospital

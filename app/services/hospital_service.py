"""
Hospital Service
Handles hospital management and nearby search operations
"""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from fastapi import HTTPException, status
# GeoAlchemy2 available for PostgreSQL; Haversine used for SQLite
from app.models import Hospital
from app.schemas.hospital import HospitalCreate, HospitalUpdate
from app.config import settings
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
            meta_data=hospital_data.metadata,
        )

        # (PostGIS location column removed for SQLite compatibility; lat/lon stored as Float)

        db.add(new_hospital)
        await db.commit()
        await db.refresh(new_hospital)

        logger.info(f"Hospital created: {new_hospital.name}")
        return new_hospital

    @staticmethod
    async def get_hospital(db: AsyncSession, hospital_id: str) -> Optional[Hospital]:
        """Get hospital by string ID"""
        result = await db.execute(select(Hospital).where(Hospital.id == str(hospital_id)))
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
        latitude: Optional[float],
        longitude: Optional[float],
        radius_km: Optional[float] = None,
        limit: int = 10,
        has_emergency_dept: Optional[bool] = None,
        has_trauma_center: Optional[bool] = None,
        has_ambulance: Optional[bool] = None,
        is_24_7: Optional[bool] = None,
    ) -> List[dict]:
        """
        Find hospitals near a location using PostGIS spatial queries with fallback support (Requirement 4)

        Args:
            db: Database session
            latitude: Location latitude
            longitude: Location longitude
            radius_km: Search radius in kilometers (defaults to admin setting)
            limit: Maximum number of results
            has_emergency_dept: Filter by emergency department availability
            has_trauma_center: Filter by trauma center availability
            has_ambulance: Filter by ambulance availability
            is_24_7: Filter by 24/7 service availability

        Returns:
            List of hospitals with distance in km and meters, ordered by distance
        """
        # Handle invalid or missing coordinates gracefully
        if latitude is None or longitude is None:
            logger.warning("Coordinates missing for hospital search")
            return []

        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            logger.warning(f"Invalid coordinates provided: lat={latitude}, lon={longitude}")
            return []

        if radius_km is None:
            radius_km = settings.HOSPITAL_SEARCH_RADIUS_KM

        # Base filter conditions
        conditions = [
            Hospital.is_active == True,
            Hospital.is_available == True,
        ]
        if has_emergency_dept is not None:
            conditions.append(Hospital.has_emergency_dept == has_emergency_dept)
        if has_trauma_center is not None:
            conditions.append(Hospital.has_trauma_center == has_trauma_center)
        if has_ambulance is not None:
            conditions.append(Hospital.has_ambulance == has_ambulance)
        if is_24_7 is not None:
            conditions.append(Hospital.is_24_7 == is_24_7)

        # Detect dialect from configured DATABASE_URL (reliable in both sync and async)
        dialect_name = "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql"


        nearby_hospitals = []

        if "sqlite" in dialect_name:
            # Python Haversine fallback for SQLite test environments
            import math
            query = select(Hospital).where(and_(*conditions))
            result = await db.execute(query)
            hospitals = result.scalars().all()

            for h in hospitals:
                # Haversine formula
                dlat = math.radians(h.latitude - latitude)
                dlon = math.radians(h.longitude - longitude)
                a = (math.sin(dlat / 2) ** 2 +
                     math.cos(math.radians(latitude)) * math.cos(math.radians(h.latitude)) *
                     math.sin(dlon / 2) ** 2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                dist_km = 6371.0 * c  # Earth radius in km

                if dist_km <= radius_km:
                    h_dict = {
                    "id": h.id,
                    "name": h.name,
                    "hospital_code": h.hospital_code,
                    "phone_numbers": h.phone_numbers or [],
                    "primary_phone": h.primary_phone,
                    "email": h.email,
                    "emergency_contact": h.emergency_contact,
                    "address": h.address,
                    "city": h.city,
                    "state": h.state,
                    "postal_code": h.postal_code,
                    "latitude": h.latitude,
                    "longitude": h.longitude,
                    "has_emergency_dept": h.has_emergency_dept,
                    "has_trauma_center": h.has_trauma_center,
                    "has_ambulance": h.has_ambulance,
                    "bed_capacity": h.bed_capacity,
                    "available_beds": h.available_beds,
                    "is_available": h.is_available,
                    "is_24_7": h.is_24_7,
                    "accepts_sms": h.accepts_sms,
                    "accepts_email": h.accepts_email,
                    "accepts_call": h.accepts_call,
                    "average_response_time_minutes": h.average_response_time_minutes,
                    "total_responses": h.total_responses,
                    "successful_responses": h.successful_responses,
                    "description": h.description,
                    "website": h.website,
                    "is_active": h.is_active,
                    "is_verified": h.is_verified,
                    "created_at": h.created_at,
                    "last_notified_at": h.last_notified_at,
                    "distance_km": round(dist_km, 2),
                    "distance_meters": round(dist_km * 1000, 1),
                }
                nearby_hospitals.append(h_dict)

            nearby_hospitals.sort(key=lambda x: x["distance_km"])
            nearby_hospitals = nearby_hospitals[:limit]

        else:
            # PostGIS spatial query for PostgreSQL
            incident_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
            distance_m = func.ST_Distance(
                Hospital.location.cast(Geography),
                incident_point.cast(Geography)
            )

            conditions.append(distance_m <= radius_km * 1000)

            query = (
                select(
                    Hospital,
                    (distance_m / 1000).label('distance_km'),
                    distance_m.label('distance_meters')
                )
                .where(and_(*conditions))
                .order_by(distance_m)
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.all()

            for hospital, dist_km, dist_m in rows:
                h_dict = {
                    "id": hospital.id,
                    "name": hospital.name,
                    "hospital_code": hospital.hospital_code,
                    "phone_numbers": hospital.phone_numbers or [],
                    "primary_phone": hospital.primary_phone,
                    "email": hospital.email,
                    "emergency_contact": hospital.emergency_contact,
                    "address": hospital.address,
                    "city": hospital.city,
                    "state": hospital.state,
                    "postal_code": hospital.postal_code,
                    "latitude": hospital.latitude,
                    "longitude": hospital.longitude,
                    "has_emergency_dept": hospital.has_emergency_dept,
                    "has_trauma_center": hospital.has_trauma_center,
                    "has_ambulance": hospital.has_ambulance,
                    "bed_capacity": hospital.bed_capacity,
                    "available_beds": hospital.available_beds,
                    "is_available": hospital.is_available,
                    "is_24_7": hospital.is_24_7,
                    "accepts_sms": hospital.accepts_sms,
                    "accepts_email": hospital.accepts_email,
                    "accepts_call": hospital.accepts_call,
                    "average_response_time_minutes": hospital.average_response_time_minutes,
                    "total_responses": hospital.total_responses,
                    "successful_responses": hospital.successful_responses,
                    "description": hospital.description,
                    "website": hospital.website,
                    "is_active": hospital.is_active,
                    "is_verified": hospital.is_verified,
                    "created_at": hospital.created_at,
                    "last_notified_at": hospital.last_notified_at,
                    "distance_km": round(dist_km, 2),
                    "distance_meters": round(dist_m, 1),
                }
                nearby_hospitals.append(h_dict)

        logger.info(f"Found {len(nearby_hospitals)} nearby hospitals within {radius_km}km")
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

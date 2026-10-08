"""
Hospital Management API Routes
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.hospital import (
    HospitalCreate,
    HospitalUpdate,
    HospitalResponse,
    HospitalListResponse,
    NearbyHospitalsRequest,
    NearbyHospitalResponse,
)
from app.models import User
from app.services.hospital_service import HospitalService
from app.dependencies import get_operator_or_admin, get_current_user, check_maintenance_mode

router = APIRouter()


@router.post("", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
async def create_hospital(
    hospital_data: HospitalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
    _: None = Depends(check_maintenance_mode),
):
    """
    Register a new hospital

    Requires operator or admin role.
    """
    hospital = await HospitalService.create_hospital(db, hospital_data)
    return hospital


@router.get("", response_model=HospitalListResponse)
async def get_hospitals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of hospitals
    """
    hospitals, total = await HospitalService.get_hospitals(db, skip, limit, is_active)

    return HospitalListResponse(
        hospitals=hospitals,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/nearby", response_model=list[NearbyHospitalResponse])
async def get_nearby_hospitals(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: Optional[float] = Query(None, gt=0, le=200),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find hospitals near a location

    Query parameters:
    - latitude: Location latitude
    - longitude: Location longitude
    - radius_km: Search radius in kilometers (optional)
    - limit: Maximum number of results (default: 10)
    """
    nearby_hospitals = await HospitalService.find_nearby_hospitals(
        db, latitude, longitude, radius_km, limit
    )

    return nearby_hospitals


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get hospital details by ID
    """
    hospital = await HospitalService.get_hospital(db, hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found"
        )
    return hospital


@router.patch("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(
    hospital_id: str,
    hospital_data: HospitalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_operator_or_admin),
    _: None = Depends(check_maintenance_mode),
):
    """
    Update hospital details

    Requires operator or admin role.
    """
    hospital = await HospitalService.update_hospital(db, hospital_id, hospital_data)
    return hospital

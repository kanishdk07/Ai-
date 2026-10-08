"""
Unit and Integration Tests for Nearby Hospital Identification (Requirement 4)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Hospital
from app.services.hospital_service import HospitalService
from app.config import settings


@pytest.fixture
async def setup_test_hospitals(db_session: AsyncSession):
    """Fixture to populate test hospitals with varied locations and service capabilities"""
    hospitals = [
        Hospital(
            name="City Central Emergency Hospital",
            hospital_code="HOSP-001",
            phone_numbers=["+919876543210"],
            email="central@emergency.org",
            emergency_contact="+919876543211",
            address="100 Highway Sector 1",
            city="Delhi",
            state="Delhi",
            postal_code="110001",
            latitude=28.7041,
            longitude=77.1025,
            has_emergency_dept=True,
            has_trauma_center=True,
            has_ambulance=True,
            is_available=True,
            is_24_7=True,
            is_active=True,
        ),
        Hospital(
            name="Suburban Trauma & Urgent Care",
            hospital_code="HOSP-002",
            phone_numbers=["+919876543220"],
            email="suburban@trauma.org",
            emergency_contact="+919876543221",
            address="205 Outer Ring Rd",
            city="Gurgaon",
            state="Haryana",
            postal_code="122001",
            latitude=28.4595,
            longitude=77.0266,
            has_emergency_dept=True,
            has_trauma_center=False,
            has_ambulance=True,
            is_available=True,
            is_24_7=True,
            is_active=True,
        ),
        Hospital(
            name="Distant General Hospital",
            hospital_code="HOSP-003",
            phone_numbers=["+919876543230"],
            email="distant@hospital.org",
            emergency_contact="+919876543231",
            address="500 Far Highway",
            city="Jaipur",
            state="Rajasthan",
            postal_code="302001",
            latitude=26.9124,
            longitude=75.7873,
            has_emergency_dept=True,
            has_trauma_center=True,
            has_ambulance=True,
            is_available=True,
            is_24_7=True,
            is_active=True,
        ),
        Hospital(
            name="Closed Clinic (Unavailable)",
            hospital_code="HOSP-004",
            phone_numbers=["+919876543240"],
            email="closed@clinic.org",
            address="12 Close St",
            city="Delhi",
            state="Delhi",
            latitude=28.7050,
            longitude=77.1030,
            has_emergency_dept=False,
            has_trauma_center=False,
            has_ambulance=False,
            is_available=False,  # Unavailable
            is_24_7=False,
            is_active=True,
        )
    ]

    for h in hospitals:
        db_session.add(h)

    await db_session.commit()
    return hospitals


@pytest.mark.asyncio
async def test_find_nearby_hospitals_distance_and_sorting(db_session: AsyncSession, setup_test_hospitals):
    """Test nearby hospital lookup calculates distance and orders results by distance ascending"""
    incident_lat = 28.7040
    incident_lon = 77.1020

    hospitals = await HospitalService.find_nearby_hospitals(
        db=db_session,
        latitude=incident_lat,
        longitude=incident_lon,
        radius_km=50.0,
        limit=10
    )

    assert len(hospitals) >= 2
    # Check distance properties
    assert "distance_km" in hospitals[0]
    assert "distance_meters" in hospitals[0]

    # Verify distance ordering (closest hospital first)
    assert hospitals[0]["distance_km"] <= hospitals[1]["distance_km"]
    assert hospitals[0]["name"] == "City Central Emergency Hospital"


@pytest.mark.asyncio
async def test_find_nearby_hospitals_service_availability_filter(db_session: AsyncSession, setup_test_hospitals):
    """Test filtering nearby hospitals by specific service capabilities"""
    hospitals = await HospitalService.find_nearby_hospitals(
        db=db_session,
        latitude=28.7041,
        longitude=77.1025,
        radius_km=50.0,
        has_trauma_center=True
    )

    for h in hospitals:
        assert h["has_trauma_center"] is True
        assert h["is_available"] is True


@pytest.mark.asyncio
async def test_find_nearby_hospitals_invalid_coordinates(db_session: AsyncSession, setup_test_hospitals):
    """Test handling missing or out-of-bounds coordinates gracefully"""
    res_none = await HospitalService.find_nearby_hospitals(db_session, latitude=None, longitude=77.1025)
    assert res_none == []

    res_invalid_lat = await HospitalService.find_nearby_hospitals(db_session, latitude=999.0, longitude=77.1025)
    assert res_invalid_lat == []

    res_invalid_lon = await HospitalService.find_nearby_hospitals(db_session, latitude=28.7041, longitude=-300.0)
    assert res_invalid_lon == []


@pytest.mark.asyncio
async def test_nearby_hospital_api_endpoint(client: AsyncClient, auth_headers: dict, setup_test_hospitals):
    """Test HTTP API endpoint for finding nearby hospitals"""
    response = await client.get(
        "/api/v1/hospitals/nearby?latitude=28.7041&longitude=77.1025&radius_km=50&limit=5",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "distance_km" in data[0]
    assert "name" in data[0]

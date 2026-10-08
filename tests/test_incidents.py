"""
Incident Tests
"""

import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_create_incident_success(client: AsyncClient):
    """Test successful incident creation (AI module endpoint)"""
    incident_data = {
        "incident_id": "TEST-001",
        "detected_at": datetime.utcnow().isoformat(),
        "accident_detected": True,
        "severity": "high",
        "confidence_score": 0.95,
        "latitude": 28.7041,
        "longitude": 77.1025,
        "location_description": "NH-48 KM 245"
    }

    response = await client.post(
        "/api/v1/incidents",
        json=incident_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"] == "TEST-001"
    assert data["severity"] == "high"
    assert data["status"] == "detected"


@pytest.mark.asyncio
async def test_create_incident_duplicate(client: AsyncClient):
    """Test duplicate incident creation"""
    incident_data = {
        "incident_id": "TEST-002",
        "detected_at": datetime.utcnow().isoformat(),
        "accident_detected": True,
        "severity": "medium",
        "confidence_score": 0.85,
    }

    # Create first incident
    response1 = await client.post("/api/v1/incidents", json=incident_data)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = await client.post("/api/v1/incidents", json=incident_data)
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_create_incident_with_idempotency_key(client: AsyncClient):
    """Test incident creation with idempotency key"""
    incident_data = {
        "incident_id": "TEST-003",
        "detected_at": datetime.utcnow().isoformat(),
        "accident_detected": True,
        "severity": "low",
        "confidence_score": 0.75,
        "idempotency_key": "unique-key-123"
    }

    # Create first incident
    response1 = await client.post("/api/v1/incidents", json=incident_data)
    assert response1.status_code == 201
    incident1_id = response1.json()["id"]

    # Retry with same idempotency key
    response2 = await client.post("/api/v1/incidents", json=incident_data)
    assert response2.status_code == 201
    incident2_id = response2.json()["id"]

    # Should return the same incident
    assert incident1_id == incident2_id


@pytest.mark.asyncio
async def test_get_incidents_list(client: AsyncClient, auth_headers: dict):
    """Test getting list of incidents"""
    # Create some test incidents first
    for i in range(3):
        await client.post(
            "/api/v1/incidents",
            json={
                "incident_id": f"TEST-LIST-{i}",
                "detected_at": datetime.utcnow().isoformat(),
                "accident_detected": True,
                "severity": "medium",
                "confidence_score": 0.80,
            }
        )

    # Get incidents list
    response = await client.get(
        "/api/v1/incidents",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "incidents" in data
    assert "total" in data
    assert data["total"] >= 3


@pytest.mark.asyncio
async def test_get_incident_by_id(client: AsyncClient, auth_headers: dict):
    """Test getting specific incident"""
    # Create incident
    create_response = await client.post(
        "/api/v1/incidents",
        json={
            "incident_id": "TEST-GET",
            "detected_at": datetime.utcnow().isoformat(),
            "accident_detected": True,
            "severity": "high",
            "confidence_score": 0.92,
        }
    )
    incident_id = create_response.json()["id"]

    # Get incident
    response = await client.get(
        f"/api/v1/incidents/{incident_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == incident_id
    assert data["incident_id"] == "TEST-GET"


@pytest.mark.asyncio
async def test_get_nonexistent_incident(client: AsyncClient, auth_headers: dict):
    """Test getting nonexistent incident"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"/api/v1/incidents/{fake_uuid}",
        headers=auth_headers
    )

    assert response.status_code == 404

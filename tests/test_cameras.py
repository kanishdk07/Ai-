"""
Camera Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_camera(client: AsyncClient, operator_headers: dict):
    """Test camera creation"""
    camera_data = {
        "camera_id": "CAM-TEST-01",
        "name": "Test Camera 1",
        "camera_type": "ip_cctv",
        "location_name": "Test Location",
        "latitude": 28.7041,
        "longitude": 77.1025,
        "description": "Test camera"
    }

    response = await client.post(
        "/api/v1/cameras",
        json=camera_data,
        headers=operator_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["camera_id"] == "CAM-TEST-01"
    assert data["name"] == "Test Camera 1"
    assert data["status"] == "offline"


@pytest.mark.asyncio
async def test_create_camera_unauthorized(client: AsyncClient, auth_headers: dict):
    """Test camera creation without proper role"""
    camera_data = {
        "camera_id": "CAM-UNAUTH",
        "name": "Unauthorized Camera",
        "camera_type": "system"
    }

    response = await client.post(
        "/api/v1/cameras",
        json=camera_data,
        headers=auth_headers  # Regular user, not operator
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_cameras_list(client: AsyncClient, operator_headers: dict, auth_headers: dict):
    """Test getting list of cameras"""
    # Create a test camera
    await client.post(
        "/api/v1/cameras",
        json={
            "camera_id": "CAM-LIST-01",
            "name": "List Test Camera",
            "camera_type": "mobile"
        },
        headers=operator_headers
    )

    # Get cameras list
    response = await client.get(
        "/api/v1/cameras",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "cameras" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_start_camera_monitoring(client: AsyncClient, operator_headers: dict):
    """Test starting camera monitoring"""
    # Create camera
    create_response = await client.post(
        "/api/v1/cameras",
        json={
            "camera_id": "CAM-START",
            "name": "Start Test Camera",
            "camera_type": "system"
        },
        headers=operator_headers
    )
    camera_id = create_response.json()["id"]

    # Start monitoring
    response = await client.post(
        f"/api/v1/cameras/{camera_id}/start",
        json={},
        headers=operator_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_monitoring"] == True
    assert data["status"] == "monitoring"

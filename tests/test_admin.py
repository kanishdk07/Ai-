"""
Admin Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_system_settings(client: AsyncClient, admin_headers: dict):
    """Test updating system settings"""
    settings_data = {
        "auto_notification_enabled": True,
        "notification_interval_seconds": 90,
        "hospital_search_radius_km": 60.0
    }

    response = await client.patch(
        "/api/v1/admin/settings",
        json=settings_data,
        headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["auto_notification_enabled"] == True
    assert data["notification_interval_seconds"] == 90


@pytest.mark.asyncio
async def test_update_settings_unauthorized(client: AsyncClient, auth_headers: dict):
    """Test updating settings without admin role"""
    response = await client.patch(
        "/api/v1/admin/settings",
        json={"auto_notification_enabled": False},
        headers=auth_headers  # Regular user
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_enable_maintenance_mode(client: AsyncClient, admin_headers: dict):
    """Test enabling maintenance mode"""
    response = await client.post(
        "/api/v1/admin/maintenance",
        json={
            "enabled": True,
            "reason": "System upgrade"
        },
        headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["maintenance_mode"] == True

    # Reset maintenance mode
    await client.post(
        "/api/v1/admin/maintenance",
        json={"enabled": False, "reason": "Test finished"},
        headers=admin_headers
    )


@pytest.mark.asyncio
async def test_system_health_check(client: AsyncClient):
    """Test system health check (no auth required)"""
    response = await client.get("/api/v1/admin/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_connected" in data
    assert "scheduler_running" in data


@pytest.mark.asyncio
async def test_emergency_stop_all(client: AsyncClient, admin_headers: dict):
    """Test emergency stop all notifications"""
    response = await client.post(
        "/api/v1/admin/notifications/stop-all",
        json={
            "reason": "Test emergency stop",
            "stop_scope": "all"
        },
        headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "stopped_count" in data
    assert "incidents_affected" in data

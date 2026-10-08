"""
Notification Tests
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from app.models import Incident, Hospital
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_manual_notification_to_phone(
    client: AsyncClient,
    operator_headers: dict,
    db_session: AsyncSession
):
    """Test sending manual notification to phone number"""
    # Create incident first
    incident_response = await client.post(
        "/api/v1/incidents",
        json={
            "incident_id": "TEST-NOTIF-001",
            "detected_at": datetime.utcnow().isoformat(),
            "accident_detected": True,
            "severity": "high",
            "confidence_score": 0.95,
            "latitude": 28.7041,
            "longitude": 77.1025,
        }
    )
    incident_id = incident_response.json()["id"]

    # Send manual notification
    notification_data = {
        "incident_id": incident_id,
        "recipient_phone": "+919876543210",
        "notification_type": "sms",
        "custom_message": "Test emergency notification"
    }

    response = await client.post(
        "/api/v1/notifications/manual",
        json=notification_data,
        headers=operator_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"] == incident_id
    assert data["recipient_phone"] == "+919876543210"
    assert data["notification_type"] == "sms"


@pytest.mark.asyncio
async def test_stop_incident_notifications(
    client: AsyncClient,
    operator_headers: dict,
    db_session: AsyncSession
):
    """Test stopping notifications for an incident"""
    # Create incident
    incident_response = await client.post(
        "/api/v1/incidents",
        json={
            "incident_id": "TEST-STOP-001",
            "detected_at": datetime.utcnow().isoformat(),
            "accident_detected": True,
            "severity": "medium",
            "confidence_score": 0.85,
        }
    )
    incident_id = incident_response.json()["id"]

    # Stop notifications
    response = await client.post(
        f"/api/v1/notifications/{incident_id}/stop",
        json={
            "reason": "Test stop",
            "stop_all_for_incident": True
        },
        headers=operator_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["incident_id"] == incident_id

"""
Comprehensive SMS Notification Integration & Scenario Unit Tests (Requirement 15)
Tests Scenario A (Live Camera), Scenario B (Uploaded Video), Idempotency, and Test Mode Delivery
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Incident, Hospital, Camera
from app.services.notification_providers import MockNotificationProvider


@pytest.mark.asyncio
async def test_scenario_a_live_camera_sms(
    client: AsyncClient,
    operator_headers: dict,
    db_session: AsyncSession
):
    """
    Test Scenario A: Live Camera Accident Notification
    - Uses camera coordinates
    - Selects nearest hospital automatically
    - Formats Scenario A message
    """
    # 1. Create camera with known GPS coordinates
    camera_id = "CAM-LIVE-HWY-01"
    cam = Camera(
        camera_id=camera_id,
        name="Highway Section A1",
        latitude=28.4595,
        longitude=77.0266,
        location_name="Highway Section A1 (KM 42)",
        status="online"
    )
    db_session.add(cam)
    await db_session.commit()

    # 2. Create hospital nearby
    hosp = Hospital(
        name="Apex Emergency Hospital",
        hospital_code="HOSP-APEX-01",
        phone_numbers=["+919876543210"],
        address="Sector 44, Gurgaon",
        latitude=28.4600,
        longitude=77.0270,
        is_active=True,
        is_available=True
    )
    db_session.add(hosp)
    await db_session.commit()

    # 3. Create live camera incident
    inc_res = await client.post(
        "/api/v1/incidents",
        json={
            "incident_id": "ACC-LIVE-001",
            "camera_external_id": camera_id,
            "detected_at": datetime.utcnow().isoformat(),
            "accident_detected": True,
            "severity": "high",
            "confidence_score": 0.94,
            "latitude": 28.4595,
            "longitude": 77.0266,
            "location_description": "Highway Section A1 (KM 42)"
        },
        headers=operator_headers
    )
    assert inc_res.status_code == 201
    inc_data = inc_res.json()

    # 4. Dispatch SMS notification
    notif_res = await client.post(
        "/api/v1/notifications/manual",
        json={
            "incident_id": inc_data["id"],
            "incident_source": "live_camera",
            "latitude": 28.4595,
            "longitude": 77.0266,
            "notification_type": "sms"
        },
        headers=operator_headers
    )

    assert notif_res.status_code == 201
    notif_data = notif_res.json()
    assert notif_data["recipient_phone"] == "+919876543210"
    assert "SAFEWAY.AI ALERT: HIGH accident detected" in notif_data["message"]
    assert "Coordinates: 28.45950, 77.02660" in notif_data["message"]
    assert "Nearest Hospital: Apex Emergency Hospital" in notif_data["message"]


@pytest.mark.asyncio
async def test_scenario_b_uploaded_video_sms(
    client: AsyncClient,
    operator_headers: dict,
    db_session: AsyncSession
):
    """
    Test Scenario B: Uploaded Video Accident Notification
    - Custom recipient phone number
    - Formats Scenario B message
    - Handles 'Location not provided' if missing
    """
    # 1. Dispatch notification for uploaded video without location
    notif_res1 = await client.post(
        "/api/v1/notifications/manual",
        json={
            "incident_id": "ACC-UPLOAD-001",
            "recipient_phone": "+919999988888",
            "incident_source": "uploaded_video",
            "notification_type": "sms"
        },
        headers=operator_headers
    )

    assert notif_res1.status_code == 201
    data1 = notif_res1.json()
    assert data1["recipient_phone"] == "+919999988888"
    assert "SAFEWAY.AI ALERT: MEDIUM accident identified in video analysis" in data1["message"]
    assert "Reported location: Location not provided" in data1["message"]

    # 2. Dispatch notification for uploaded video with explicit location
    notif_res2 = await client.post(
        "/api/v1/notifications/manual",
        json={
            "incident_id": "ACC-UPLOAD-002",
            "recipient_phone": "+919999988888",
            "incident_source": "uploaded_video",
            "location_description": "NH-48 Gurgaon Exit 9",
            "notification_type": "sms"
        },
        headers=operator_headers
    )

    assert notif_res2.status_code == 201
    data2 = notif_res2.json()
    assert "Reported location: NH-48 Gurgaon Exit 9" in data2["message"]


@pytest.mark.asyncio
async def test_camera_missing_location_sms(
    client: AsyncClient,
    operator_headers: dict,
    db_session: AsyncSession
):
    """
    Test Live Camera Incident without Location
    - Formats message with 'Camera location unavailable'
    """
    notif_res = await client.post(
        "/api/v1/notifications/manual",
        json={
            "incident_id": "ACC-NOLOC-001",
            "recipient_phone": "+919876543210",
            "incident_source": "live_camera",
            "notification_type": "sms"
        },
        headers=operator_headers
    )

    assert notif_res.status_code == 201
    data = notif_res.json()
    assert "Location: Camera location unavailable" in data["message"]


@pytest.mark.asyncio
async def test_idempotency_duplicate_notification_suppression(
    client: AsyncClient,
    operator_headers: dict,
    db_session: AsyncSession
):
    """
    Test Idempotency / Duplicate Notification Suppression
    - Repeated requests for same incident and recipient within window update repeat_sequence
    """
    req_payload = {
        "incident_id": "ACC-IDEM-001",
        "recipient_phone": "+919876543210",
        "incident_source": "live_camera",
        "notification_type": "sms"
    }

    # First request
    res1 = await client.post("/api/v1/notifications/manual", json=req_payload, headers=operator_headers)
    assert res1.status_code == 201
    data1 = res1.json()

    # Immediate second request
    res2 = await client.post("/api/v1/notifications/manual", json=req_payload, headers=operator_headers)
    assert res2.status_code == 201
    data2 = res2.json()

    assert data2["id"] == data1["id"]
    assert data2["is_repeat"] is True
    assert data2["repeat_sequence"] > 1


@pytest.mark.asyncio
async def test_mock_sms_provider_delivery():
    """
    Test Mock SMS Provider Unit Delivery Result
    """
    provider = MockNotificationProvider()
    res = await provider.send_sms(to_phone="+919876543210", message="Test alert message")
    assert res.success is True
    assert res.provider_name == "mock"
    assert "MOCK-SMS-" in res.provider_message_id

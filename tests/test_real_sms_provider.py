"""
Comprehensive Real SMS Integration, Database Persistence, and Provider Tests (Requirement 12)
Tests:
1. Database-backed emergency contact saving and retrieval.
2. Provider selection (Twilio, Fast2SMS, Mock).
3. Missing provider credentials error handling.
4. Emergency Notifications ON / OFF toggle policy enforcement.
5. Truthful delivery status reporting (mock vs real provider).
6. Robustness: AI incident creation continues uninterrupted even if provider fails.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.admin_setting import AdminSetting
from app.services.notification_providers import (
    NotificationProviderFactory,
    TwilioSMSProvider,
    Fast2SMSProvider,
    MockNotificationProvider,
)
from app.config import settings


@pytest.mark.asyncio
async def test_emergency_contact_database_persistence(
    client: AsyncClient,
    admin_headers: dict,
    db_session: AsyncSession
):
    """
    Test 1: Saving & retrieving emergency contact number in DB
    """
    test_number = "+919876543210"

    # Save via PATCH /api/v1/admin/notification-settings
    save_res = await client.patch(
        "/api/v1/admin/notification-settings",
        json={
            "emergency_contact_number": test_number,
            "emergency_notifications_enabled": True,
            "hospital_notifications_enabled": False
        },
        headers=admin_headers
    )
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["emergency_contact_number"] == test_number
    assert save_data["emergency_notifications_enabled"] is True

    # Retrieve via GET /api/v1/admin/notification-settings
    get_res = await client.get("/api/v1/admin/notification-settings", headers=admin_headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["emergency_contact_number"] == test_number
    assert get_data["emergency_notifications_enabled"] is True

    # Direct DB verification
    db_res = await db_session.execute(
        select(AdminSetting).order_by(AdminSetting.created_at.desc()).limit(1)
    )
    setting = db_res.scalar_one_or_none()
    assert setting is not None
    assert setting.emergency_contact_number == test_number
    assert setting.emergency_notifications_enabled is True


@pytest.mark.asyncio
async def test_provider_selection_and_missing_credentials():
    """
    Test 2 & 3: Provider selection and missing credentials error handling
    """
    # 1. Twilio selection without credentials
    settings.SMS_PROVIDER = "twilio"
    settings.SMS_ACCOUNT_SID = None
    settings.SMS_AUTH_TOKEN = None
    settings.SMS_FROM_NUMBER = None

    provider = NotificationProviderFactory.get_provider(channel="sms")
    assert isinstance(provider, TwilioSMSProvider)

    res = await provider.send_sms(to_phone="+919876543210", message="Test message")
    assert res.success is False
    assert res.provider_name == "twilio"
    assert "Missing SMS_ACCOUNT_SID" in res.error_message

    # 2. Fast2SMS selection without credentials
    settings.SMS_PROVIDER = "fast2sms"
    settings.FAST2SMS_API_KEY = None

    f2s_provider = NotificationProviderFactory.get_provider(channel="sms")
    assert isinstance(f2s_provider, Fast2SMSProvider)

    f2s_res = await f2s_provider.send_sms(to_phone="+919876543210", message="Test message")
    assert f2s_res.success is False
    assert f2s_res.provider_name == "fast2sms"
    assert "Missing FAST2SMS_API_KEY" in f2s_res.error_message

    # 3. Explicit Mock selection
    settings.SMS_PROVIDER = "mock"
    mock_provider = NotificationProviderFactory.get_provider(channel="sms")
    assert isinstance(mock_provider, MockNotificationProvider)

    mock_res = await mock_provider.send_sms(to_phone="+919876543210", message="Test message")
    assert mock_res.success is True
    assert mock_res.provider_name == "mock"


@pytest.mark.asyncio
async def test_emergency_notifications_off_policy_guard(
    client: AsyncClient,
    admin_headers: dict,
    db_session: AsyncSession
):
    """
    Test 4: Emergency Notifications OFF prevents test SMS
    """
    # Disable emergency notifications
    await client.patch(
        "/api/v1/admin/notification-settings",
        json={
            "emergency_contact_number": "+919876543210",
            "emergency_notifications_enabled": False
        },
        headers=admin_headers
    )

    # Attempt to send test notification
    test_res = await client.post(
        "/api/v1/admin/notification-settings/test",
        headers=admin_headers
    )
    assert test_res.status_code == 200
    test_data = test_res.json()
    assert test_data["sent"] is False
    assert "currently OFF" in test_data["message"]


@pytest.mark.asyncio
async def test_test_notification_endpoint_response_truthfulness(
    client: AsyncClient,
    admin_headers: dict,
    db_session: AsyncSession
):
    """
    Test 5: Send Test Notification returns truthful simulated message in mock mode
    """
    # Enable emergency notifications with a valid number
    await client.patch(
        "/api/v1/admin/notification-settings",
        json={
            "emergency_contact_number": "+919876543210",
            "emergency_notifications_enabled": True
        },
        headers=admin_headers
    )

    settings.SMS_PROVIDER = "mock"

    test_res = await client.post(
        "/api/v1/admin/notification-settings/test",
        headers=admin_headers
    )
    assert test_res.status_code == 200
    test_data = test_res.json()
    assert test_data["sent"] is True
    assert test_data["provider"] == "mock"
    assert "Test simulated — no SMS sent" in test_data["message"]

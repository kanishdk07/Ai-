"""
Notification Providers Module
Provides common notification provider interface and concrete implementations for:
- Twilio SMS
- Firebase Cloud Messaging (FCM)
- SendGrid Email
- Mock Notification Provider (for test/development mode)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationDeliveryResult:
    """Standard container for notification delivery status and provider metadata"""

    def __init__(
        self,
        success: bool,
        provider_name: str,
        provider_message_id: Optional[str] = None,
        provider_response: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        self.success = success
        self.provider_name = provider_name
        self.provider_message_id = provider_message_id
        self.provider_response = provider_response or {}
        self.error_message = error_message
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "provider_name": self.provider_name,
            "provider_message_id": self.provider_message_id,
            "provider_response": self.provider_response,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseNotificationProvider(ABC):
    """Abstract Base Class for all Notification Providers"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the notification provider"""
        pass

    @abstractmethod
    async def send_sms(
        self,
        to_phone: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        """Send SMS notification"""
        pass

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        """Send Email notification"""
        pass

    @abstractmethod
    async def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        """Send Push notification via FCM/APNS"""
        pass


class MockNotificationProvider(BaseNotificationProvider):
    """Mock Provider for local testing, development, and unit tests"""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def send_sms(
        self,
        to_phone: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        logger.info(f"[MOCK SMS] Sent to '{to_phone}': {message}")
        msg_id = f"MOCK-SMS-{int(datetime.utcnow().timestamp())}"
        return NotificationDeliveryResult(
            success=True,
            provider_name=self.provider_name,
            provider_message_id=msg_id,
            provider_response={"status": "mock_delivered", "recipient": to_phone},
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        logger.info(f"[MOCK EMAIL] Sent to '{to_email}' - Subject: '{subject}'")
        msg_id = f"MOCK-EMAIL-{int(datetime.utcnow().timestamp())}"
        return NotificationDeliveryResult(
            success=True,
            provider_name=self.provider_name,
            provider_message_id=msg_id,
            provider_response={"status": "mock_delivered", "recipient": to_email},
        )

    async def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        logger.info(f"[MOCK PUSH] Sent to device '{device_token}' - Title: '{title}'")
        msg_id = f"MOCK-PUSH-{int(datetime.utcnow().timestamp())}"
        return NotificationDeliveryResult(
            success=True,
            provider_name=self.provider_name,
            provider_message_id=msg_id,
            provider_response={"status": "mock_delivered", "device": device_token},
        )


class TwilioSMSProvider(BaseNotificationProvider):
    """Twilio SMS API Provider Integration"""

    def __init__(self):
        self.account_sid = settings.SMS_ACCOUNT_SID
        self.auth_token = settings.SMS_AUTH_TOKEN
        self.from_number = settings.SMS_FROM_NUMBER

    @property
    def provider_name(self) -> str:
        return "twilio"

    async def send_sms(
        self,
        to_phone: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        if not self.account_sid or not self.auth_token or not self.from_number:
            logger.error("Twilio SMS credentials missing (SMS_ACCOUNT_SID, SMS_AUTH_TOKEN, SMS_FROM_NUMBER)")
            return NotificationDeliveryResult(
                success=False,
                provider_name=self.provider_name,
                error_message="Twilio configuration error: Missing SMS_ACCOUNT_SID, SMS_AUTH_TOKEN, or SMS_FROM_NUMBER in backend environment variables."
            )

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        data = {
            "To": to_phone,
            "From": self.from_number,
            "Body": message
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self.account_sid, self.auth_token)
                )

            res_json = response.json()
            if response.status_code in [200, 201]:
                return NotificationDeliveryResult(
                    success=True,
                    provider_name=self.provider_name,
                    provider_message_id=res_json.get("sid"),
                    provider_response=res_json,
                )
            else:
                err = res_json.get("message", response.text)
                return NotificationDeliveryResult(
                    success=False,
                    provider_name=self.provider_name,
                    provider_response=res_json,
                    error_message=f"Twilio API error ({response.status_code}): {err}"
                )

        except Exception as e:
            logger.error(f"Twilio SMS request exception: {str(e)}")
            return NotificationDeliveryResult(
                success=False,
                provider_name=self.provider_name,
                error_message=f"Twilio HTTP exception: {str(e)}"
            )

    async def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> NotificationDeliveryResult:
        return await MockNotificationProvider().send_email(to_email, subject, body_text, body_html, metadata)

    async def send_push(self, device_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> NotificationDeliveryResult:
        return await MockNotificationProvider().send_push(device_token, title, body, data, metadata)


class Fast2SMSProvider(BaseNotificationProvider):
    """Fast2SMS API Provider Integration for Indian Regional SMS Delivery"""

    def __init__(self):
        self.api_key = settings.FAST2SMS_API_KEY

    @property
    def provider_name(self) -> str:
        return "fast2sms"

    async def send_sms(
        self,
        to_phone: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        if not self.api_key:
            logger.error("Fast2SMS API key missing (FAST2SMS_API_KEY)")
            return NotificationDeliveryResult(
                success=False,
                provider_name=self.provider_name,
                error_message="Fast2SMS configuration error: Missing FAST2SMS_API_KEY in backend environment variables."
            )

        clean_numbers = "".join(filter(str.isdigit, to_phone))
        if len(clean_numbers) > 10 and clean_numbers.startswith("91"):
            clean_numbers = clean_numbers[2:]

        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "route": "q",
            "message": message,
            "language": "english",
            "flash": 0,
            "numbers": clean_numbers
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)

            res_json = response.json()
            if response.status_code == 200 and res_json.get("return") is True:
                msg_ids = res_json.get("request_id") or (res_json.get("message", ["FAST2SMS-SENT"])[0] if isinstance(res_json.get("message"), list) else "FAST2SMS-SENT")
                return NotificationDeliveryResult(
                    success=True,
                    provider_name=self.provider_name,
                    provider_message_id=str(msg_ids),
                    provider_response=res_json,
                )
            else:
                err = res_json.get("message", response.text)
                return NotificationDeliveryResult(
                    success=False,
                    provider_name=self.provider_name,
                    provider_response=res_json,
                    error_message=f"Fast2SMS API error ({response.status_code}): {err}"
                )
        except Exception as e:
            logger.error(f"Fast2SMS request exception: {str(e)}")
            return NotificationDeliveryResult(
                success=False,
                provider_name=self.provider_name,
                error_message=f"Fast2SMS HTTP exception: {str(e)}"
            )

    async def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> NotificationDeliveryResult:
        return await MockNotificationProvider().send_email(to_email, subject, body_text, body_html, metadata)

    async def send_push(self, device_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> NotificationDeliveryResult:
        return await MockNotificationProvider().send_push(device_token, title, body, data, metadata)


class FCMNotificationProvider(BaseNotificationProvider):
    """Firebase Cloud Messaging (FCM) API Provider Integration"""

    def __init__(self):
        self.server_key = settings.FCM_SERVER_KEY
        self.project_id = settings.FCM_PROJECT_ID

    @property
    def provider_name(self) -> str:
        return "firebase"

    async def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        if settings.TEST_MODE or not settings.FCM_ENABLED or not self.server_key:
            logger.info(f"[FCM TEST MODE] Simulating FCM push to device {device_token}")
            return await MockNotificationProvider().send_push(device_token, title, body, data, metadata)

        url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "to": device_token,
            "notification": {"title": title, "body": body},
            "data": data or {}
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)

            res_json = response.json()
            if response.status_code == 200 and res_json.get("success", 0) > 0:
                msg_id = str(res_json.get("results", [{}])[0].get("message_id", ""))
                return NotificationDeliveryResult(
                    success=True,
                    provider_name=self.provider_name,
                    provider_message_id=msg_id,
                    provider_response=res_json,
                )
            else:
                return NotificationDeliveryResult(
                    success=False,
                    provider_name=self.provider_name,
                    provider_response=res_json,
                    error_message=f"FCM error: {res_json}"
                )
        except Exception as e:
            logger.error(f"FCM push request exception: {str(e)}")
            return NotificationDeliveryResult(
                success=False,
                provider_name=self.provider_name,
                error_message=str(e)
            )

    async def send_sms(self, to_phone: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationDeliveryResult:
        return await MockNotificationProvider().send_sms(to_phone, message, metadata)

    async def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> NotificationDeliveryResult:
        return await MockNotificationProvider().send_email(to_email, subject, body_text, body_html, metadata)


class SendGridEmailProvider(BaseNotificationProvider):
    """SendGrid Email API Provider Integration"""

    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.SENDGRID_FROM_EMAIL or settings.EMAIL_FROM

    @property
    def provider_name(self) -> str:
        return "sendgrid"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationDeliveryResult:
        if settings.TEST_MODE or not settings.SENDGRID_ENABLED or not self.api_key:
            logger.info(f"[SENDGRID TEST MODE] Simulating Email to {to_email}")
            return await MockNotificationProvider().send_email(to_email, subject, body_text, body_html, metadata)

        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        content = [{"type": "text/plain", "value": body_text}]
        if body_html:
            content.append({"type": "text/html", "value": body_html})

        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": self.from_email},
            "subject": subject,
            "content": content
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)

            if response.status_code in [200, 202]:
                msg_id = response.headers.get("X-Message-Id", f"SG-{int(datetime.utcnow().timestamp())}")
                return NotificationDeliveryResult(
                    success=True,
                    provider_name=self.provider_name,
                    provider_message_id=msg_id,
                    provider_response={"status_code": response.status_code},
                )
            else:
                return NotificationDeliveryResult(
                    success=False,
                    provider_name=self.provider_name,
                    error_message=f"SendGrid API error ({response.status_code}): {response.text}"
                )
        except Exception as e:
            logger.error(f"SendGrid email request exception: {str(e)}")
            return NotificationDeliveryResult(
                success=False,
                provider_name=self.provider_name,
                error_message=str(e)
            )

    async def send_sms(self, to_phone: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationDeliveryResult:
        return await MockNotificationProvider().send_sms(to_phone, message, metadata)

    async def send_push(self, device_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> NotificationDeliveryResult:
        return await MockNotificationProvider().send_push(device_token, title, body, data, metadata)


class NotificationProviderFactory:
    """Factory class to provide notification providers seamlessly"""

    @staticmethod
    def get_provider(
        channel: str = "sms",
        test_mode: Optional[bool] = None
    ) -> BaseNotificationProvider:
        """
        Get provider instance for requested notification channel.
        Explicitly respects SMS_PROVIDER setting ('twilio', 'fast2sms', 'mock').
        """
        channel_lower = (channel or "sms").lower()

        if channel_lower == "sms":
            provider_setting = (settings.SMS_PROVIDER or "twilio").lower()

            if provider_setting == "twilio":
                return TwilioSMSProvider()
            elif provider_setting in ["fast2sms", "fastsms"]:
                return Fast2SMSProvider()
            elif provider_setting == "mock":
                return MockNotificationProvider()

            # If TEST_MODE is explicitly enabled and provider is unconfigured, return mock
            if settings.TEST_MODE and not settings.SMS_ACCOUNT_SID and not settings.FAST2SMS_API_KEY:
                return MockNotificationProvider()

            return TwilioSMSProvider()

        elif channel_lower == "push":
            if settings.FCM_ENABLED and settings.FCM_SERVER_KEY:
                return FCMNotificationProvider()
            return MockNotificationProvider()

        elif channel_lower == "email":
            if settings.SENDGRID_ENABLED and settings.SENDGRID_API_KEY:
                return SendGridEmailProvider()
            return MockNotificationProvider()

        return MockNotificationProvider()

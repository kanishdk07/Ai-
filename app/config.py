"""
Application Configuration
Manages environment variables and application settings
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Highway Accident Detection System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True

    # Notification System
    AUTO_NOTIFICATION_ENABLED: bool = False
    NOTIFICATION_INTERVAL_SECONDS: int = 60
    MIN_NOTIFICATION_INTERVAL: int = 30
    MAX_NOTIFICATION_INTERVAL: int = 300
    MAX_NOTIFICATION_RETRIES: int = 10

    # Hospital Search
    HOSPITAL_SEARCH_RADIUS_KM: float = 50.0
    MAX_HOSPITALS_TO_NOTIFY: int = 5

    # Incident Configuration
    INCIDENT_AUTO_RESOLVE_HOURS: int = 24
    HIGH_SEVERITY_THRESHOLD: float = 0.8
    MEDIUM_SEVERITY_THRESHOLD: float = 0.5

    # Camera Configuration
    CAMERA_HEALTH_CHECK_INTERVAL_SECONDS: int = 300
    CAMERA_TIMEOUT_SECONDS: int = 30

    # System Mode
    MAINTENANCE_MODE: bool = False
    TEST_MODE: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # SMS/Notification Provider
    SMS_PROVIDER: Optional[str] = "twilio"
    SMS_ACCOUNT_SID: Optional[str] = None
    SMS_AUTH_TOKEN: Optional[str] = None
    SMS_FROM_NUMBER: Optional[str] = None
    FAST2SMS_API_KEY: Optional[str] = None
    TEXTBELT_API_KEY: Optional[str] = "textbelt"
    TEXTBEE_API_KEY: Optional[str] = None
    TEXTBEE_DEVICE_ID: Optional[str] = None

    # Firebase Cloud Messaging
    FCM_ENABLED: bool = False
    FCM_SERVER_KEY: Optional[str] = None
    FCM_PROJECT_ID: Optional[str] = None
    FCM_CREDENTIALS_FILE: Optional[str] = None

    # SendGrid Email Configuration
    SENDGRID_ENABLED: bool = False
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[str] = None

    # Email Configuration
    EMAIL_ENABLED: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # Webhook
    WEBHOOK_VERIFICATION_TOKEN: Optional[str] = None

    # Admin
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "ChangeThisPassword123!"

    # File / Image Storage
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"
    IMAGE_STORAGE_PATH: str = "uploads/images"
    IMAGE_SERVE_SECURE: bool = True

    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100

    # Timezone
    TIMEZONE: str = "UTC"

    # Performance
    WORKER_PROCESSES: int = 4
    KEEP_ALIVE_TIMEOUT: int = 65

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses lru_cache to ensure settings are loaded once
    """
    return Settings()


# Global settings instance
settings = get_settings()

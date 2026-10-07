"""
Validators
Custom validation functions for data validation
"""

import re
import phonenumbers
from typing import Optional
from datetime import datetime


def validate_phone_number(phone: str, country: str = "IN") -> bool:
    """
    Validate phone number using phonenumbers library

    Args:
        phone: Phone number string
        country: Country code (default: IN for India)

    Returns:
        True if valid, False otherwise
    """
    try:
        parsed = phonenumbers.parse(phone, country)
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False


def format_phone_number(phone: str, country: str = "IN") -> Optional[str]:
    """
    Format phone number to international format

    Args:
        phone: Phone number string
        country: Country code

    Returns:
        Formatted phone number or None if invalid
    """
    try:
        parsed = phonenumbers.parse(phone, country)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return None
    except phonenumbers.NumberParseException:
        return None


def validate_latitude(lat: float) -> bool:
    """
    Validate latitude value

    Args:
        lat: Latitude value

    Returns:
        True if valid (-90 to 90)
    """
    return -90 <= lat <= 90


def validate_longitude(lon: float) -> bool:
    """
    Validate longitude value

    Args:
        lon: Longitude value

    Returns:
        True if valid (-180 to 180)
    """
    return -180 <= lon <= 180


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate both latitude and longitude

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        True if both are valid
    """
    return validate_latitude(lat) and validate_longitude(lon)


def validate_incident_id(incident_id: str) -> bool:
    """
    Validate incident ID format

    Args:
        incident_id: Incident ID string

    Returns:
        True if valid format
    """
    # Allow alphanumeric, hyphens, underscores, 1-100 chars
    pattern = r'^[a-zA-Z0-9_-]{1,100}$'
    return bool(re.match(pattern, incident_id))


def validate_camera_id(camera_id: str) -> bool:
    """
    Validate camera ID format

    Args:
        camera_id: Camera ID string

    Returns:
        True if valid format
    """
    # Allow alphanumeric, hyphens, underscores, 1-100 chars
    pattern = r'^[a-zA-Z0-9_-]{1,100}$'
    return bool(re.match(pattern, camera_id))


def validate_confidence_score(score: float) -> bool:
    """
    Validate confidence score is between 0.0 and 1.0

    Args:
        score: Confidence score

    Returns:
        True if valid (0.0 to 1.0)
    """
    return 0.0 <= score <= 1.0


def validate_url(url: str) -> bool:
    """
    Basic URL validation

    Args:
        url: URL string

    Returns:
        True if valid URL format
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(url_pattern.match(url))


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    Sanitize user input string

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not text:
        return ""

    # Remove null bytes and control characters
    sanitized = ''.join(char for char in text if char.isprintable() or char.isspace())

    # Trim to max length
    return sanitized[:max_length].strip()


def validate_datetime_range(start: datetime, end: datetime) -> bool:
    """
    Validate that end datetime is after start datetime

    Args:
        start: Start datetime
        end: End datetime

    Returns:
        True if end is after start
    """
    return end > start

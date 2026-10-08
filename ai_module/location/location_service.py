"""
GPS & Camera Location Registry and Location Manager
Associates detected events with trusted location data across manual video uploads, mobile cameras, and registered CCTV.
Strictly enforces location verification status without inventing fake GPS coordinates.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Dict, Optional, Tuple, Any

from ai_module.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LocationData:
    latitude: Optional[float]
    longitude: Optional[float]
    location_description: Optional[str] = None
    accuracy_m: Optional[float] = None
    timestamp: Optional[str] = None
    is_verified: bool = False
    location_status: str = "unavailable"  # "verified", "registered", "stale", "unavailable"
    source: str = "unavailable"  # "mobile_gps", "registered_camera", "provided_gps", "user_provided", "unavailable"

    def to_dict(self) -> Dict[str, Any]:
        """Format location metadata according to API contract."""
        data: Dict[str, Any] = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_status": self.location_status,
            "source": self.source,
            "is_verified": self.is_verified
        }
        if self.accuracy_m is not None:
            data["accuracy_m"] = self.accuracy_m
        if self.timestamp is not None:
            data["timestamp"] = self.timestamp
        if self.location_description:
            data["location_description"] = self.location_description
        return data


class LocationRegistry:
    """
    Unified Location Metadata Manager for Registered Cameras, Mobile Device Stream, and Uploaded Videos.
    """

    def __init__(self, max_location_age_seconds: float = settings.MAX_LOCATION_AGE_SECONDS):
        self.camera_locations: Dict[str, LocationData] = {}
        self.latest_mobile_locations: Dict[str, Tuple[LocationData, float]] = {}  # device/cam_id -> (LocData, time.time())
        self.max_location_age = max_location_age_seconds

    def register_camera_location(
        self,
        camera_id: str,
        latitude: float,
        longitude: float,
        location_description: Optional[str] = None
    ):
        """Register fixed spatial coordinates for a system or IP camera."""
        loc = LocationData(
            latitude=float(latitude),
            longitude=float(longitude),
            location_description=location_description or f"Registered Camera [{camera_id}]",
            is_verified=True,
            location_status="registered",
            source="registered_camera"
        )
        self.camera_locations[camera_id] = loc
        logger.info(f"Registered spatial coordinates for Camera [{camera_id}]: ({latitude}, {longitude})")

    def update_mobile_location(
        self,
        camera_or_device_id: str,
        latitude: float,
        longitude: float,
        accuracy_m: Optional[float] = None,
        timestamp_str: Optional[str] = None,
        location_description: Optional[str] = None
    ):
        """Update active mobile device GPS coordinates received over HTTP/WebSocket."""
        import time
        now_iso = timestamp_str or datetime.now(timezone.utc).isoformat()
        loc = LocationData(
            latitude=float(latitude),
            longitude=float(longitude),
            location_description=location_description or f"Mobile Device GPS ({latitude:.4f}, {longitude:.4f})",
            accuracy_m=float(accuracy_m) if accuracy_m is not None else None,
            timestamp=now_iso,
            is_verified=True,
            location_status="verified",
            source="mobile_gps"
        )
        self.latest_mobile_locations[camera_or_device_id] = (loc, time.time())
        logger.info(f"Updated live mobile GPS for [{camera_or_device_id}]: ({latitude}, {longitude})")

    def resolve_location(
        self,
        camera_id: str,
        override_gps: Optional[Dict[str, Any]] = None,
        source_type: str = "live"
    ) -> LocationData:
        """
        Resolve location for an event adhering to location priority rules:
        1. Trusted explicit GPS provided with payload (provided_gps / user_provided)
        2. Authorized recent mobile device GPS (mobile_gps, checking max age)
        3. Registered camera coordinates (registered_camera)
        4. Fallback unavailable location (latitude=None, longitude=None, location_status='unavailable')
        """
        import time

        # 1. Check explicit override / payload GPS
        if override_gps and isinstance(override_gps, dict):
            lat = override_gps.get("latitude")
            lng = override_gps.get("longitude")
            if lat is not None and lng is not None:
                try:
                    f_lat = float(lat)
                    f_lng = float(lng)
                    source = override_gps.get("source", "provided_gps" if source_type == "uploaded_video" else "mobile_gps")
                    status = override_gps.get("location_status", "verified")
                    desc = override_gps.get("location_description") or f"Provided Location ({f_lat:.4f}, {f_lng:.4f})"
                    return LocationData(
                        latitude=f_lat,
                        longitude=f_lng,
                        location_description=desc,
                        accuracy_m=float(override_gps["accuracy_m"]) if "accuracy_m" in override_gps else None,
                        timestamp=str(override_gps.get("timestamp")) if "timestamp" in override_gps else None,
                        is_verified=True,
                        location_status=status,
                        source=source
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid override GPS coordinates: {override_gps} ({e})")

        # 2. Check live mobile location registry
        if camera_id in self.latest_mobile_locations:
            mobile_loc, rec_time = self.latest_mobile_locations[camera_id]
            age = time.time() - rec_time
            if age <= self.max_location_age:
                return mobile_loc
            else:
                logger.warning(f"Mobile GPS for [{camera_id}] is stale (age: {age:.1f}s > {self.max_location_age}s).")
                # Mark as stale if no registered fallback
                if camera_id not in self.camera_locations:
                    stale_loc = LocationData(
                        latitude=mobile_loc.latitude,
                        longitude=mobile_loc.longitude,
                        location_description=f"{mobile_loc.location_description} (Stale)",
                        is_verified=False,
                        location_status="stale",
                        source="mobile_gps"
                    )
                    return stale_loc

        # 3. Check registered static camera coordinates
        if camera_id in self.camera_locations:
            return self.camera_locations[camera_id]

        # 4. Fallback unavailable location: DO NOT invent fake coordinates
        logger.info(f"Location unavailable for stream/event [{camera_id}]. Coordinates missing.")
        return LocationData(
            latitude=None,
            longitude=None,
            location_description="Location Unavailable",
            is_verified=False,
            location_status="unavailable",
            source="unavailable"
        )

"""
GPS & Camera Location Registry and Resolver
Associates detected events with registered camera GPS coordinates or mobile device location data.
Maintains strict verification flags and formatted location metadata for backend integration.
"""

from dataclasses import dataclass
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LocationData:
    latitude: Optional[float]
    longitude: Optional[float]
    location_description: Optional[str]
    is_verified: bool
    source: str  # "registered_camera", "mobile_gps", "external_api", "unverified"


class LocationRegistry:
    """
    Registry for camera locations and device GPS resolver.
    """

    def __init__(self):
        # Default registered camera locations mapping: camera_id -> LocationData
        self.camera_locations: Dict[str, LocationData] = {}

    def register_camera_location(
        self,
        camera_id: str,
        latitude: float,
        longitude: float,
        location_description: str
    ):
        """Register fixed spatial coordinates for a system or IP camera."""
        loc = LocationData(
            latitude=float(latitude),
            longitude=float(longitude),
            location_description=location_description,
            is_verified=True,
            source="registered_camera"
        )
        self.camera_locations[camera_id] = loc
        logger.info(f"Registered spatial coordinates for Camera [{camera_id}]: ({latitude}, {longitude})")

    def resolve_location(
        self,
        camera_id: str,
        override_gps: Optional[Dict[str, float]] = None
    ) -> LocationData:
        """
        Resolve location for an event.
        Priority:
        1. Explicit authorized mobile device GPS coordinates passed with stream/frame
        2. Registered static coordinates for camera_id
        3. Unverified missing location fallback
        """
        # 1. Check mobile / stream override GPS
        if override_gps and "latitude" in override_gps and "longitude" in override_gps:
            try:
                lat = float(override_gps["latitude"])
                lng = float(override_gps["longitude"])
                desc = override_gps.get("location_description", f"Mobile Device GPS ({lat:.4f}, {lng:.4f})")
                return LocationData(
                    latitude=lat,
                    longitude=lng,
                    location_description=desc,
                    is_verified=True,
                    source="mobile_gps"
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid mobile GPS coordinates format: {override_gps} ({e})")

        # 2. Check registered camera spatial coordinates
        if camera_id in self.camera_locations:
            return self.camera_locations[camera_id]

        # 3. Unverified location fallback (do not invent fake coordinates)
        logger.warning(f"Location unverified for Camera [{camera_id}]. Coordinates missing.")
        return LocationData(
            latitude=None,
            longitude=None,
            location_description=f"Camera [{camera_id}] - Location Unverified",
            is_verified=False,
            source="unverified"
        )

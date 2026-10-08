"""
Google Maps Service
Handles integration with Google Maps API (Geocoding, Distance Matrix, Maps URLs)
"""

import httpx
import logging
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Service for Google Maps API integration"""

    GEOCODE_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    DISTANCE_MATRIX_API_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
    STATIC_MAP_API_URL = "https://maps.googleapis.com/maps/api/staticmap"

    @staticmethod
    def is_enabled() -> bool:
        """Check if Google Maps API integration is enabled and key is configured"""
        return bool(settings.GOOGLE_MAPS_ENABLED and settings.GOOGLE_MAPS_API_KEY)

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Get the configured Google Maps API Key"""
        return settings.GOOGLE_MAPS_API_KEY

    @staticmethod
    def get_directions_url(
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        travel_mode: str = "driving",
    ) -> str:
        """
        Generate a Google Maps Directions web/mobile URL
        
        Args:
            origin_lat: Latitude of origin (e.g. incident location)
            origin_lng: Longitude of origin
            destination_lat: Latitude of destination (e.g. hospital)
            destination_lng: Longitude of destination
            travel_mode: Mode of travel (driving, walking, transit, bicycling)
            
        Returns:
            Google Maps directions URL string
        """
        params = {
            "api": "1",
            "origin": f"{origin_lat},{origin_lng}",
            "destination": f"{destination_lat},{destination_lng}",
            "travelmode": travel_mode,
        }
        return f"https://www.google.com/maps/dir/?{urlencode(params)}"

    @staticmethod
    def get_embed_map_url(
        latitude: float,
        longitude: float,
        zoom: int = 15,
        map_type: str = "roadmap",
    ) -> str:
        """
        Generate Google Maps Embed URL for UI iframe components
        """
        key = settings.GOOGLE_MAPS_API_KEY or ""
        params = {
            "key": key,
            "q": f"{latitude},{longitude}",
            "zoom": str(zoom),
            "maptype": map_type,
        }
        return f"https://www.google.com/maps/embed/v1/place?{urlencode(params)}"

    @staticmethod
    def get_static_map_url(
        latitude: float,
        longitude: float,
        zoom: int = 15,
        width: int = 600,
        height: int = 400,
        markers: bool = True,
    ) -> str:
        """
        Generate Google Maps Static Map image URL
        """
        key = settings.GOOGLE_MAPS_API_KEY or ""
        params = {
            "center": f"{latitude},{longitude}",
            "zoom": str(zoom),
            "size": f"{width}x{height}",
            "maptype": "roadmap",
            "key": key,
        }
        if markers:
            params["markers"] = f"color:red|label:A|{latitude},{longitude}"
        return f"{GoogleMapsService.STATIC_MAP_API_URL}?{urlencode(params)}"

    @staticmethod
    async def reverse_geocode(
        latitude: float,
        longitude: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Convert latitude/longitude to a human-readable address using Google Geocoding API
        """
        if not GoogleMapsService.is_enabled():
            logger.warning("Google Maps API is disabled or API key is missing")
            return None

        params = {
            "latlng": f"{latitude},{longitude}",
            "key": settings.GOOGLE_MAPS_API_KEY,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(GoogleMapsService.GEOCODE_API_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "OK" and data.get("results"):
                    first_result = data["results"][0]
                    return {
                        "formatted_address": first_result.get("formatted_address"),
                        "address_components": first_result.get("address_components", []),
                        "place_id": first_result.get("place_id"),
                        "raw": data,
                    }
                else:
                    logger.error(f"Google Geocoding API error status: {data.get('status')} - {data.get('error_message')}")
                    return None
        except Exception as e:
            logger.error(f"Error calling Google Geocoding API: {e}")
            return None

    @staticmethod
    async def calculate_road_distance(
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "driving",
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate actual road driving distance and estimated time using Google Distance Matrix API
        """
        if not GoogleMapsService.is_enabled():
            logger.warning("Google Maps API disabled or API key missing")
            return None

        params = {
            "origins": f"{origin_lat},{origin_lng}",
            "destinations": f"{dest_lat},{dest_lng}",
            "mode": mode,
            "key": settings.GOOGLE_MAPS_API_KEY,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(GoogleMapsService.DISTANCE_MATRIX_API_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "OK" and data.get("rows"):
                    element = data["rows"][0]["elements"][0]
                    if element.get("status") == "OK":
                        distance_meters = element["distance"]["value"]
                        duration_seconds = element["duration"]["value"]
                        return {
                            "distance_km": round(distance_meters / 1000.0, 2),
                            "distance_text": element["distance"]["text"],
                            "duration_minutes": round(duration_seconds / 60.0, 1),
                            "duration_text": element["duration"]["text"],
                        }
                    else:
                        logger.warning(f"Distance Matrix element status: {element.get('status')}")
                        return None
                else:
                    logger.error(f"Distance Matrix API status: {data.get('status')} - {data.get('error_message')}")
                    return None
        except Exception as e:
            logger.error(f"Error calling Google Distance Matrix API: {e}")
            return None

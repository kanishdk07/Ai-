"""
Google Maps API Routes
Provides endpoints for Google Maps integration, geocoding, distance calculations, and URLs.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from app.models import User
from app.dependencies import get_current_user
from app.services.google_maps_service import GoogleMapsService
from app.config import settings

router = APIRouter()


class MapsConfigResponse(BaseModel):
    """Schema for Google Maps status configuration"""
    enabled: bool
    api_key_configured: bool
    default_search_radius_km: float


class GeocodeResponse(BaseModel):
    """Schema for reverse geocode response"""
    formatted_address: Optional[str] = None
    place_id: Optional[str] = None


class DistanceMatrixResponse(BaseModel):
    """Schema for road distance calculation response"""
    distance_km: float
    distance_text: str
    duration_minutes: float
    duration_text: str


class DirectionsUrlResponse(BaseModel):
    """Schema for Google Maps Directions URL response"""
    directions_url: str
    embed_url: str
    static_map_url: str


@router.get("/config", response_model=MapsConfigResponse)
async def get_maps_config(
    current_user: User = Depends(get_current_user),
):
    """
    Get Google Maps API integration configuration status
    """
    return MapsConfigResponse(
        enabled=settings.GOOGLE_MAPS_ENABLED,
        api_key_configured=bool(settings.GOOGLE_MAPS_API_KEY),
        default_search_radius_km=settings.HOSPITAL_SEARCH_RADIUS_KM,
    )


@router.get("/geocode", response_model=GeocodeResponse)
async def reverse_geocode_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
):
    """
    Convert latitude and longitude into address using Google Geocoding API
    """
    if not GoogleMapsService.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Maps API key is not configured or disabled"
        )

    result = await GoogleMapsService.reverse_geocode(latitude, longitude)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not geocode the specified coordinates"
        )

    return GeocodeResponse(
        formatted_address=result.get("formatted_address"),
        place_id=result.get("place_id"),
    )


@router.get("/distance", response_model=DistanceMatrixResponse)
async def calculate_driving_distance(
    origin_latitude: float = Query(..., ge=-90, le=90),
    origin_longitude: float = Query(..., ge=-180, le=180),
    destination_latitude: float = Query(..., ge=-90, le=90),
    destination_longitude: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate driving distance and time between origin and destination using Google Distance Matrix API
    """
    if not GoogleMapsService.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Maps API key is not configured or disabled"
        )

    result = await GoogleMapsService.calculate_road_distance(
        origin_lat=origin_latitude,
        origin_lng=origin_longitude,
        dest_lat=destination_latitude,
        dest_lng=destination_longitude,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not calculate driving distance between specified coordinates"
        )

    return DistanceMatrixResponse(**result)


@router.get("/directions-url", response_model=DirectionsUrlResponse)
async def get_directions_and_map_urls(
    origin_latitude: float = Query(..., ge=-90, le=90),
    origin_longitude: float = Query(..., ge=-180, le=180),
    destination_latitude: float = Query(..., ge=-90, le=90),
    destination_longitude: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
):
    """
    Get Google Maps directions URL, embed URL, and static map URL for navigation
    """
    directions_url = GoogleMapsService.get_directions_url(
        origin_lat=origin_latitude,
        origin_lng=origin_longitude,
        destination_lat=destination_latitude,
        destination_lng=destination_longitude,
    )

    embed_url = GoogleMapsService.get_embed_map_url(
        latitude=destination_latitude,
        longitude=destination_longitude,
    )

    static_map_url = GoogleMapsService.get_static_map_url(
        latitude=destination_latitude,
        longitude=destination_longitude,
    )

    return DirectionsUrlResponse(
        directions_url=directions_url,
        embed_url=embed_url,
        static_map_url=static_map_url,
    )

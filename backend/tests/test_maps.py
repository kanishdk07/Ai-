"""
Tests for Google Maps API service and routes
"""

import pytest
from httpx import AsyncClient
from app.services.google_maps_service import GoogleMapsService
from app.config import settings


@pytest.mark.asyncio
async def test_maps_config_endpoint(client: AsyncClient, auth_headers: dict):
    """Test getting Google Maps configuration status"""
    response = await client.get("/api/v1/maps/config", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "api_key_configured" in data
    assert "default_search_radius_km" in data


@pytest.mark.asyncio
async def test_directions_url_generation():
    """Test Google Maps directions and map URLs generation"""
    origin_lat, origin_lng = 28.7041, 77.1025
    dest_lat, dest_lng = 28.7141, 77.1125

    directions_url = GoogleMapsService.get_directions_url(
        origin_lat, origin_lng, dest_lat, dest_lng
    )
    assert "google.com/maps/dir/" in directions_url
    assert f"{origin_lat},{origin_lng}" in directions_url
    assert f"{dest_lat},{dest_lng}" in directions_url

    embed_url = GoogleMapsService.get_embed_map_url(dest_lat, dest_lng)
    assert "google.com/maps/embed/v1/place" in embed_url
    assert f"{dest_lat},{dest_lng}" in embed_url

    static_map_url = GoogleMapsService.get_static_map_url(dest_lat, dest_lng)
    assert "googleapis.com/maps/api/staticmap" in static_map_url
    assert f"{dest_lat},{dest_lng}" in static_map_url


@pytest.mark.asyncio
async def test_directions_url_endpoint(client: AsyncClient, auth_headers: dict):
    """Test /api/v1/maps/directions-url endpoint"""
    params = {
        "origin_latitude": 28.7041,
        "origin_longitude": 77.1025,
        "destination_latitude": 28.7141,
        "destination_longitude": 77.1125,
    }
    response = await client.get("/api/v1/maps/directions-url", params=params, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "directions_url" in data
    assert "embed_url" in data
    assert "static_map_url" in data

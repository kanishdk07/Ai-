"""
API v1 Package
"""
from fastapi import APIRouter
from app.api.v1 import auth, cameras, incidents, hospitals, notifications, admin, websocket, maps

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["Cameras"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(hospitals.router, prefix="/hospitals", tags=["Hospitals"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(maps.router, prefix="/maps", tags=["Google Maps"])

__all__ = ["api_router"]

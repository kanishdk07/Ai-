"""
Camera Input Package
Provides unified input streams for system webcams, mobile streams, and external RTSP/IP cameras.
"""

from .base import BaseCameraStream, FrameData, CameraStatus, StreamHealth
from .system_camera import SystemCameraStream, list_available_cameras
from .mobile_camera import MobileCameraStream
from .external_camera import ExternalIPCameraStream
from .manager import CameraInputManager

__all__ = [
    "BaseCameraStream",
    "FrameData",
    "CameraStatus",
    "StreamHealth",
    "SystemCameraStream",
    "list_available_cameras",
    "MobileCameraStream",
    "ExternalIPCameraStream",
    "CameraInputManager",
]

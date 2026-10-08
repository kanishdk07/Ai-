"""
Unified Camera Input Manager
Registers, manages, and orchestrates heterogeneous camera inputs (system webcams, mobile streams, RTSP cameras).
Provides a single unified stream consumption interface to the AI accident detection pipeline.
"""

import logging
from typing import Dict, Optional, List
from .base import BaseCameraStream, FrameData, StreamHealth, CameraStatus
from .system_camera import SystemCameraStream
from .mobile_camera import MobileCameraStream
from .external_camera import ExternalIPCameraStream

logger = logging.getLogger(__name__)


class CameraInputManager:
    """
    Manager for registering and retrieving frames from all active camera streams.
    """

    def __init__(self):
        self.streams: Dict[str, BaseCameraStream] = {}

    def register_stream(self, stream: BaseCameraStream) -> bool:
        """Register a custom or standard camera stream implementation."""
        if stream.camera_id in self.streams:
            logger.warning(f"Overwriting existing camera stream [{stream.camera_id}]")
            self.stop_stream(stream.camera_id)
        self.streams[stream.camera_id] = stream
        logger.info(f"Registered camera stream [{stream.camera_id}] of type '{stream.camera_type}'")
        return True

    def register_system_camera(self, camera_id: str, device_index: int = 0) -> SystemCameraStream:
        """Register a local system webcam/USB camera."""
        stream = SystemCameraStream(camera_id=camera_id, device_index=device_index)
        self.register_stream(stream)
        return stream

    def register_mobile_camera(self, camera_id: str) -> MobileCameraStream:
        """Register a mobile camera stream receiver."""
        stream = MobileCameraStream(camera_id=camera_id)
        self.register_stream(stream)
        return stream

    def register_external_camera(
        self,
        camera_id: str,
        stream_url: str,
        connection_config: Optional[dict] = None
    ) -> ExternalIPCameraStream:
        """Register an RTSP or IP camera stream."""
        stream = ExternalIPCameraStream(
            camera_id=camera_id,
            stream_url=stream_url,
            connection_config=connection_config
        )
        self.register_stream(stream)
        return stream

    def register_file_camera(
        self,
        camera_id: str,
        file_path: str,
        loop: bool = True
    ) -> ExternalIPCameraStream:
        """Register a recorded video file stream for incident testing & simulation."""
        stream = ExternalIPCameraStream(
            camera_id=camera_id,
            stream_url=file_path,
            is_file_loop=loop
        )
        self.register_stream(stream)
        return stream

    def start_all(self) -> Dict[str, bool]:
        """Start all registered camera streams."""
        results = {}
        for cam_id, stream in self.streams.items():
            results[cam_id] = stream.start()
        return results

    def start_stream(self, camera_id: str) -> bool:
        """Start a specific stream."""
        if camera_id not in self.streams:
            logger.error(f"Camera ID [{camera_id}] not registered.")
            return False
        return self.streams[camera_id].start()

    def pause_stream(self, camera_id: str) -> None:
        """Pause a specific stream."""
        if camera_id in self.streams:
            self.streams[camera_id].pause()

    def resume_stream(self, camera_id: str) -> None:
        """Resume a specific stream."""
        if camera_id in self.streams:
            self.streams[camera_id].resume()

    def stop_stream(self, camera_id: str) -> None:
        """Stop a specific stream."""
        if camera_id in self.streams:
            self.streams[camera_id].stop()

    def stop_all(self) -> None:
        """Stop all registered camera streams."""
        for cam_id, stream in list(self.streams.items()):
            stream.stop()
        logger.info("All camera streams stopped.")

    def read_frame(self, camera_id: str) -> Optional[FrameData]:
        """Read latest frame from a specific camera stream."""
        if camera_id not in self.streams:
            return None
        return self.streams[camera_id].read_frame()

    def get_stream(self, camera_id: str) -> Optional[BaseCameraStream]:
        """Get stream instance by camera ID."""
        return self.streams.get(camera_id)

    def get_active_camera_ids(self) -> List[str]:
        """Get list of camera IDs currently online or monitoring."""
        return [
            cam_id for cam_id, stream in self.streams.items()
            if stream.status in [CameraStatus.ONLINE, CameraStatus.RECONNECTING]
        ]

    def get_all_health(self) -> Dict[str, StreamHealth]:
        """Get health status of all streams."""
        return {cam_id: stream.get_health() for cam_id, stream in self.streams.items()}

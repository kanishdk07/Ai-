"""
External CCTV / IP Camera & RTSP Stream Interface
Processes RTSP, HTTP/MJPEG, and video file streams using OpenCV / FFmpeg.
Secure credential masking, connection status monitoring, and automatic reconnection.
"""

import time
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
import cv2
import numpy as np

from .base import BaseCameraStream, FrameData, CameraStatus

logger = logging.getLogger(__name__)


def mask_rtsp_url(url: str) -> str:
    """Mask credentials in RTSP URLs for secure logging."""
    if not url:
        return ""
    # Pattern to match rtsp://user:pass@host:port/path
    masked = re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)
    return masked


class ExternalIPCameraStream(BaseCameraStream):
    """
    External IP Camera / RTSP stream handler.
    Supports RTSP, HTTP, HTTPS, ONVIF stream URLs, and offline video file playback.
    """

    def __init__(
        self,
        camera_id: str,
        stream_url: str,
        connection_config: Optional[Dict[str, Any]] = None,
        target_fps: float = 25.0,
        reconnect_attempts: int = 10,
        reconnect_delay: float = 3.0,
        is_file_loop: bool = False
    ):
        super().__init__(camera_id=camera_id, camera_type="ip_cctv")
        self.stream_url = stream_url
        self.connection_config = connection_config or {}
        self.target_fps = target_fps
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.is_file_loop = is_file_loop

        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_counter = 0
        self.consecutive_failures = 0
        self.max_failures_before_reconnect = 15
        self.last_frame_time = 0.0

    def start(self) -> bool:
        """Establish connection to RTSP / IP stream."""
        masked_url = mask_rtsp_url(self.stream_url)
        logger.info(f"Connecting to External Camera [{self.camera_id}] at {masked_url}")

        try:
            # Set OpenCV FFmpeg RTSP flags if applicable
            # Reduce buffer latency for RTSP streams
            import os
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|buffer_size;102400"

            self.cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)

            if not self.cap.isOpened():
                # Fallback to standard capture
                self.cap = cv2.VideoCapture(self.stream_url)

            if not self.cap.isOpened():
                self.status = CameraStatus.ERROR
                self.health.error_message = f"Could not connect to RTSP/IP stream: {masked_url}"
                logger.error(self.health.error_message)
                return False

            self.status = CameraStatus.ONLINE
            self.health.error_message = None
            self.consecutive_failures = 0
            logger.info(f"Successfully connected to External Camera [{self.camera_id}]")
            return True

        except Exception as e:
            self.status = CameraStatus.ERROR
            self.health.error_message = f"Stream connection exception: {str(e)}"
            logger.error(f"External Camera [{self.camera_id}] error: {e}")
            return False

    def pause(self) -> None:
        """Pause processing stream."""
        self.is_paused = True
        self.status = CameraStatus.PAUSED

    def resume(self) -> None:
        """Resume stream processing."""
        self.is_paused = False
        if self.is_connected():
            self.status = CameraStatus.ONLINE

    def stop(self) -> None:
        """Stop external camera stream and close connection."""
        self.status = CameraStatus.OFFLINE
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info(f"External Camera [{self.camera_id}] connection closed.")

    def is_connected(self) -> bool:
        """Verify underlying connection state."""
        return self.cap is not None and self.cap.isOpened() and self.status == CameraStatus.ONLINE

    def _attempt_reconnect(self) -> bool:
        """Re-establish RTSP stream connection."""
        self.status = CameraStatus.RECONNECTING
        self.health.reconnect_attempts += 1
        masked_url = mask_rtsp_url(self.stream_url)
        logger.warning(
            f"RTSP stream loss for [{self.camera_id}] ({masked_url}). Attempt {self.health.reconnect_attempts}/{self.reconnect_attempts}..."
        )

        if self.cap:
            self.cap.release()

        time.sleep(self.reconnect_delay)
        if self.start():
            logger.info(f"External Camera [{self.camera_id}] reconnected.")
            return True
        return False

    def read_frame(self) -> Optional[FrameData]:
        """Read frame from IP camera / RTSP stream."""
        if self.is_paused or self.status == CameraStatus.OFFLINE:
            return None

        if not self.is_connected():
            if self.health.reconnect_attempts < self.reconnect_attempts:
                if not self._attempt_reconnect():
                    return None
            else:
                self.status = CameraStatus.ERROR
                return None

        ret, frame = self.cap.read()
        now = datetime.now(timezone.utc)

        if not ret or frame is None:
            # Handle video file end of file looping for test simulation
            if self.is_file_loop and self.cap:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()

            if not ret or frame is None:
                self.consecutive_failures += 1
                self.health.dropped_frames += 1
                if self.consecutive_failures >= self.max_failures_before_reconnect:
                    self._attempt_reconnect()
                return None

        self.consecutive_failures = 0
        self.frame_counter += 1
        self.health.total_frames += 1
        self.health.last_frame_timestamp = now

        # Calculate actual stream FPS
        current_time = time.time()
        if self.last_frame_time > 0:
            dt = current_time - self.last_frame_time
            if dt > 0:
                self.health.fps = 1.0 / dt
        self.last_frame_time = current_time

        h, w = frame.shape[:2]

        return FrameData(
            frame_id=self.frame_counter,
            image=frame,
            timestamp=now,
            camera_id=self.camera_id,
            camera_type="ip_cctv",
            width=w,
            height=h,
            fps=self.health.fps,
            metadata={"masked_url": mask_rtsp_url(self.stream_url)}
        )

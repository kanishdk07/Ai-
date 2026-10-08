"""
System Camera Stream
Implementation for OpenCV local webcams and USB system cameras.
Supports device enumeration, start/pause/stop, and safe auto-reconnection.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Union
import cv2
import numpy as np

from .base import BaseCameraStream, FrameData, CameraStatus

logger = logging.getLogger(__name__)


def list_available_cameras(max_devices: int = 5) -> List[int]:
    """
    Probe available local system camera device indices.
    Returns list of working camera index integers.
    """
    available = []
    for i in range(max_devices):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if cv2.__name__ and 'win' in cv2.__name__ else cv2.CAP_ANY)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(i)
            cap.release()
    return available


class SystemCameraStream(BaseCameraStream):
    """
    OpenCV webcam/system camera capture module.
    """

    def __init__(
        self,
        camera_id: str,
        device_index: Union[int, str] = 0,
        target_fps: float = 30.0,
        reconnect_attempts: int = 5,
        reconnect_delay: float = 2.0
    ):
        super().__init__(camera_id=camera_id, camera_type="system")
        self.device_index = device_index
        self.target_fps = target_fps
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay

        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_counter = 0
        self.consecutive_failures = 0
        self.max_failures_before_reconnect = 10
        self.last_frame_time = 0.0

    def start(self) -> bool:
        """Initialize webcam connection."""
        logger.info(f"Starting System Camera [{self.camera_id}] on device {self.device_index}")
        try:
            self.cap = cv2.VideoCapture(self.device_index)
            if not self.cap.isOpened():
                self.status = CameraStatus.ERROR
                self.health.error_message = f"Failed to open system device {self.device_index}"
                logger.error(self.health.error_message)
                return False

            self.status = CameraStatus.ONLINE
            self.health.error_message = None
            self.consecutive_failures = 0
            return True
        except Exception as e:
            self.status = CameraStatus.ERROR
            self.health.error_message = str(e)
            logger.error(f"Error starting system camera [{self.camera_id}]: {e}")
            return False

    def pause(self) -> None:
        """Pause capture stream."""
        self.is_paused = True
        self.status = CameraStatus.PAUSED
        logger.info(f"System Camera [{self.camera_id}] paused.")

    def resume(self) -> None:
        """Resume capture stream."""
        self.is_paused = False
        if self.is_connected():
            self.status = CameraStatus.ONLINE
        logger.info(f"System Camera [{self.camera_id}] resumed.")

    def stop(self) -> None:
        """Stop and release camera resource."""
        self.status = CameraStatus.OFFLINE
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info(f"System Camera [{self.camera_id}] stopped and released.")

    def is_connected(self) -> bool:
        """Check if VideoCapture is opened and healthy."""
        return self.cap is not None and self.cap.isOpened() and self.status == CameraStatus.ONLINE

    def _attempt_reconnect(self) -> bool:
        """Attempt safe reconnection after stream loss."""
        self.status = CameraStatus.RECONNECTING
        self.health.reconnect_attempts += 1
        logger.warning(
            f"Camera [{self.camera_id}] disconnected. Reconnection attempt {self.health.reconnect_attempts}/{self.reconnect_attempts}..."
        )

        if self.cap:
            self.cap.release()

        time.sleep(self.reconnect_delay)
        if self.start():
            logger.info(f"Camera [{self.camera_id}] successfully reconnected.")
            return True
        return False

    def read_frame(self) -> Optional[FrameData]:
        """Read latest frame from webcam."""
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
            self.consecutive_failures += 1
            self.health.dropped_frames += 1
            if self.consecutive_failures >= self.max_failures_before_reconnect:
                logger.warning(f"System camera [{self.camera_id}] hit consecutive frame failures.")
                self._attempt_reconnect()
            return None

        self.consecutive_failures = 0
        self.frame_counter += 1
        self.health.total_frames += 1
        self.health.last_frame_timestamp = now

        # Calculate FPS
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
            camera_type="system",
            width=w,
            height=h,
            fps=self.health.fps,
            metadata={"device_index": self.device_index}
        )

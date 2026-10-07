"""
Mobile Camera Stream & Transport Interface
Processes stream frames pushed from mobile browser or mobile web apps over HTTP/WebSockets.
Handles variable frame rates, variable resolutions, network dropouts, and mobile GPS metadata.
"""

import base64
import logging
import queue
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
import cv2
import numpy as np

from .base import BaseCameraStream, FrameData, CameraStatus

logger = logging.getLogger(__name__)


class MobileCameraStream(BaseCameraStream):
    """
    Mobile browser/app stream receiver.
    Frames are pushed asynchronously to `push_frame()` by an HTTP server or WebSocket handler.
    """

    def __init__(
        self,
        camera_id: str,
        buffer_size: int = 30,
        inactivity_timeout_seconds: float = 10.0
    ):
        super().__init__(camera_id=camera_id, camera_type="mobile")
        self.frame_queue: queue.Queue = queue.Queue(maxsize=buffer_size)
        self.inactivity_timeout = inactivity_timeout_seconds
        self.frame_counter = 0
        self.last_received_time = 0.0

    def start(self) -> bool:
        """Mark mobile stream as active and ready to receive frames."""
        self.status = CameraStatus.ONLINE
        self.health.error_message = None
        logger.info(f"Mobile Camera Stream [{self.camera_id}] activated.")
        return True

    def pause(self) -> None:
        """Pause processing incoming frames."""
        self.is_paused = True
        self.status = CameraStatus.PAUSED

    def resume(self) -> None:
        """Resume processing incoming frames."""
        self.is_paused = False
        self.status = CameraStatus.ONLINE

    def stop(self) -> None:
        """Stop mobile stream processor and clear frame queue."""
        self.status = CameraStatus.OFFLINE
        with self.frame_queue.mutex:
            self.frame_queue.queue.clear()
        logger.info(f"Mobile Camera Stream [{self.camera_id}] stopped.")

    def is_connected(self) -> bool:
        """Check if mobile stream is active and received frames recently."""
        if self.status != CameraStatus.ONLINE:
            return False
        if self.last_received_time > 0 and (time.time() - self.last_received_time) > self.inactivity_timeout:
            self.status = CameraStatus.RECONNECTING
            return False
        return True

    def push_frame(
        self,
        frame_input: Union[bytes, str, np.ndarray],
        timestamp: Optional[datetime] = None,
        gps_coords: Optional[Dict[str, float]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Frontend-to-Backend Video Transport Entry point.
        Accepts:
        - raw JPEG/PNG image bytes
        - base64 encoded string ("data:image/jpeg;base64,...")
        - NumPy BGR array
        """
        if self.status == CameraStatus.OFFLINE:
            self.start()

        now = timestamp or datetime.now(timezone.utc)
        image_np: Optional[np.ndarray] = None

        try:
            if isinstance(frame_input, np.ndarray):
                image_np = frame_input
            elif isinstance(frame_input, str):
                if "," in frame_input:
                    frame_input = frame_input.split(",", 1)[1]
                img_bytes = base64.b64decode(frame_input)
                nparr = np.frombuffer(img_bytes, np.uint8)
                image_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif isinstance(frame_input, bytes):
                nparr = np.frombuffer(frame_input, np.uint8)
                image_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image_np is None or image_np.size == 0:
                logger.warning(f"Mobile Stream [{self.camera_id}] received invalid frame bytes.")
                self.health.dropped_frames += 1
                return False

            self.last_received_time = time.time()
            self.status = CameraStatus.ONLINE
            self.frame_counter += 1

            h, w = image_np.shape[:2]

            metadata = extra_metadata or {}
            if gps_coords:
                metadata["gps"] = gps_coords

            frame_data = FrameData(
                frame_id=self.frame_counter,
                image=image_np,
                timestamp=now,
                camera_id=self.camera_id,
                camera_type="mobile",
                width=w,
                height=h,
                fps=self.health.fps,
                metadata=metadata
            )

            # Put frame into queue, dropping oldest if full to avoid lag
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                    self.health.dropped_frames += 1
                except queue.Empty:
                    pass

            self.frame_queue.put_nowait(frame_data)
            self.health.total_frames += 1
            self.health.last_frame_timestamp = now
            return True

        except Exception as e:
            logger.error(f"Failed to decode pushed frame for Mobile Camera [{self.camera_id}]: {e}")
            self.health.dropped_frames += 1
            return False

    def read_frame(self) -> Optional[FrameData]:
        """Read latest pushed frame from buffer."""
        if self.is_paused or self.status == CameraStatus.OFFLINE:
            return None

        # Check for stream inactivity
        if self.last_received_time > 0 and (time.time() - self.last_received_time) > self.inactivity_timeout:
            self.status = CameraStatus.RECONNECTING

        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

"""
Base Camera Stream Specification
Defines unified interface, data structures, and status enums for all camera input types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import enum
from typing import Optional, Dict, Any
import numpy as np


class CameraStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    RECONNECTING = "reconnecting"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class StreamHealth:
    status: CameraStatus = CameraStatus.OFFLINE
    fps: float = 0.0
    dropped_frames: int = 0
    total_frames: int = 0
    reconnect_attempts: int = 0
    last_frame_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class FrameData:
    frame_id: int
    image: np.ndarray  # BGR frame matrix
    timestamp: datetime
    camera_id: str
    camera_type: str  # "system", "mobile", "ip_cctv", "file"
    width: int
    height: int
    fps: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCameraStream(ABC):
    """
    Unified abstract camera stream interface.
    All camera inputs (webcam, mobile transport, RTSP IP camera, video file) implement this interface.
    """

    def __init__(self, camera_id: str, camera_type: str):
        self.camera_id = camera_id
        self.camera_type = camera_type
        self.status = CameraStatus.OFFLINE
        self.health = StreamHealth(status=CameraStatus.OFFLINE)
        self.is_paused = False

    @abstractmethod
    def start(self) -> bool:
        """Initialize and start the camera stream."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause frame capture."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume frame capture."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop stream and release camera resources."""
        pass

    @abstractmethod
    def read_frame(self) -> Optional[FrameData]:
        """Read the next frame from the stream buffer."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if camera stream is active and connected."""
        pass

    def get_health(self) -> StreamHealth:
        """Get stream health metrics."""
        self.health.status = self.status
        return self.health

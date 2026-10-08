"""
Unit Tests for Camera Input Manager and Stream Classes
"""

import numpy as np
import pytest
from datetime import datetime, timezone

from ai_module.camera import (
    CameraInputManager,
    SystemCameraStream,
    MobileCameraStream,
    ExternalIPCameraStream,
    CameraStatus
)


def test_camera_manager_registration():
    mgr = CameraInputManager()
    sys_cam = mgr.register_system_camera("CAM-SYS-01", device_index=0)
    mob_cam = mgr.register_mobile_camera("CAM-MOB-01")
    ext_cam = mgr.register_external_camera("CAM-EXT-01", "rtsp://admin:secret@192.168.1.100:554/live")

    assert len(mgr.streams) == 3
    assert mgr.get_stream("CAM-SYS-01").camera_type == "system"
    assert mgr.get_stream("CAM-MOB-01").camera_type == "mobile"
    assert mgr.get_stream("CAM-EXT-01").camera_type == "ip_cctv"


def test_mobile_camera_stream_push():
    stream = MobileCameraStream("CAM-MOB-TEST")
    stream.start()
    assert stream.status == CameraStatus.ONLINE

    # Create dummy BGR image
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)

    # Push NumPy frame with GPS metadata
    gps_coords = {"latitude": 37.7749, "longitude": -122.4194}
    pushed = stream.push_frame(dummy_img, gps_coords=gps_coords)
    assert pushed is True

    frame_data = stream.read_frame()
    assert frame_data is not None
    assert frame_data.camera_id == "CAM-MOB-TEST"
    assert frame_data.width == 640
    assert frame_data.height == 480
    assert frame_data.metadata.get("gps") == gps_coords


def test_external_camera_masked_url():
    stream = ExternalIPCameraStream("CAM-RTSP", "rtsp://admin:pass123@10.0.0.1:554/stream1")
    health = stream.get_health()
    assert health.status == CameraStatus.OFFLINE
    assert stream.camera_id == "CAM-RTSP"

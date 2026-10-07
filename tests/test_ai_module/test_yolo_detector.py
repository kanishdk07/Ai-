"""
Unit Tests for YOLO11 Vehicle Detector
"""

import numpy as np
import pytest
from datetime import datetime, timezone

from ai_module.detection import YOLO11Detector, DetectedVehicle


def test_detector_initialization():
    detector = YOLO11Detector(conf_threshold=0.30, inference_size=320)
    assert detector.conf_threshold == 0.30
    assert detector.imgsz == 320


def test_vehicle_detection_on_frame():
    detector = YOLO11Detector(conf_threshold=0.25)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Draw white rectangle simulating a vehicle blob
    dummy_frame[100:300, 150:400] = 255

    now = datetime.now(timezone.utc)
    res = detector.detect(dummy_frame, frame_id=1, timestamp=now, camera_id="CAM-TEST")

    assert res.frame_id == 1
    assert res.camera_id == "CAM-TEST"
    assert isinstance(res.vehicle_count, int)
    assert isinstance(res.inference_time_ms, float)
    assert res.resolution == (640, 480)

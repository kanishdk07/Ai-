"""
Unit Tests for Vehicle Tracking, Trajectory Analysis, and Collision Detection
"""

from datetime import datetime, timezone, timedelta
import pytest

from ai_module.detection import DetectedVehicle
from ai_module.tracking import MultiObjectVehicleTracker
from ai_module.collision import CollisionAnalyzer, CollisionStatus


def test_tracker_assigns_persistent_ids():
    tracker = MultiObjectVehicleTracker(iou_threshold=0.2)
    now = datetime.now(timezone.utc)

    # Frame 1: Two vehicles
    v1 = DetectedVehicle(box=(100.0, 100.0, 200.0, 200.0), confidence=0.85, class_id=2, class_name="car")
    v2 = DetectedVehicle(box=(300.0, 300.0, 400.0, 400.0), confidence=0.90, class_id=7, class_name="truck")

    tracked_f1 = tracker.update([v1, v2], frame_id=1, timestamp=now)
    assert len(tracked_f1) == 2
    id1, id2 = tracked_f1[0].track_id, tracked_f1[1].track_id
    assert id1 is not None and id2 is not None and id1 != id2

    # Frame 2: Slightly moved vehicles
    now2 = now + timedelta(seconds=0.1)
    v1_next = DetectedVehicle(box=(105.0, 105.0, 205.0, 205.0), confidence=0.85, class_id=2, class_name="car")
    v2_next = DetectedVehicle(box=(305.0, 305.0, 405.0, 405.0), confidence=0.90, class_id=7, class_name="truck")

    tracked_f2 = tracker.update([v1_next, v2_next], frame_id=2, timestamp=now2)
    assert tracked_f2[0].track_id == id1
    assert tracked_f2[1].track_id == id2


def test_collision_analyzer_candidate_and_confirmation():
    analyzer = CollisionAnalyzer(confirmation_frames=2, cooldown_seconds=5.0)
    tracker = MultiObjectVehicleTracker()

    cam_id = "CAM-COLLISION-TEST"
    base_time = datetime.now(timezone.utc)

    # Simulate 5 consecutive frames where two vehicles collide (high overlap & abrupt stop)
    for frame_i in range(1, 6):
        ts = base_time + timedelta(seconds=frame_i * 0.1)

        # Overlapping bounding boxes
        v1 = DetectedVehicle(box=(100.0, 100.0, 250.0, 250.0), confidence=0.9, class_id=2, class_name="car")
        v2 = DetectedVehicle(box=(120.0, 120.0, 260.0, 260.0), confidence=0.9, class_id=2, class_name="car")

        tracked = tracker.update([v1, v2], frame_id=frame_i, timestamp=ts)
        confirmed_evt, candidate_evts = analyzer.analyze_frame(
            camera_id=cam_id,
            frame_id=frame_i,
            timestamp=ts,
            detected_vehicles=tracked,
            tracker=tracker
        )

        if frame_i == 1:
            assert len(candidate_evts) >= 1
            assert candidate_evts[0].status == CollisionStatus.CANDIDATE
            assert confirmed_evt is None
        elif frame_i >= 2 and confirmed_evt is not None:
            assert confirmed_evt.status == CollisionStatus.CONFIRMED
            assert confirmed_evt.confidence_score > 0.40
            assert len(confirmed_evt.vehicles) == 2
            break

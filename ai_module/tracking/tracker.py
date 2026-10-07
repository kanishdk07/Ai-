"""
Multi-Object Vehicle Tracker
Provides persistent object tracking across frames using IoU + Centroid Kalman multi-object tracking algorithm.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import numpy as np

from ai_module.detection.yolo_detector import DetectedVehicle


@dataclass
class TrackedVehicleState:
    track_id: int
    class_id: int
    class_name: str
    current_box: Tuple[float, float, float, float]
    confidence: float
    last_seen_frame: int
    positions: List[Tuple[float, float, datetime]] = field(default_factory=list)  # (cx, cy, timestamp)
    velocities: List[Tuple[float, float]] = field(default_factory=list)          # (vx_px_per_sec, vy_px_per_sec)
    speed_history: List[float] = field(default_factory=list)                     # speed_px_per_sec

    def update(self, box: Tuple[float, float, float, float], confidence: float, frame_id: int, timestamp: datetime):
        self.current_box = box
        self.confidence = confidence
        self.last_seen_frame = frame_id

        cx = (box[0] + box[2]) / 2.0
        cy = (box[1] + box[3]) / 2.0

        # Update position history
        self.positions.append((cx, cy, timestamp))
        if len(self.positions) > 60:  # Keep 60 frames max history
            self.positions.pop(0)

        # Calculate velocity
        if len(self.positions) >= 2:
            prev_cx, prev_cy, prev_t = self.positions[-2]
            dt = (timestamp - prev_t).total_seconds()
            if dt > 0:
                vx = (cx - prev_cx) / dt
                vy = (cy - prev_cy) / dt
                speed = float(np.hypot(vx, vy))
                self.velocities.append((vx, vy))
                self.speed_history.append(speed)
                if len(self.velocities) > 60:
                    self.velocities.pop(0)
                    self.speed_history.pop(0)

    @property
    def current_speed(self) -> float:
        """Get latest speed in pixels per second."""
        return self.speed_history[-1] if self.speed_history else 0.0

    @property
    def average_recent_speed(self) -> float:
        """Average speed over past N frames."""
        if not self.speed_history:
            return 0.0
        recent = self.speed_history[-10:]
        return float(np.mean(recent))


class MultiObjectVehicleTracker:
    """
    IoU + Centroid Vehicle Tracker.
    Maintains vehicle IDs and computes velocity vectors over time.
    """

    def __init__(self, iou_threshold: float = 0.3, max_disappeared: int = 15):
        self.iou_threshold = iou_threshold
        self.max_disappeared = max_disappeared
        self.next_track_id = 1
        self.tracked_vehicles: Dict[int, TrackedVehicleState] = {}

    def update(
        self,
        detected_vehicles: List[DetectedVehicle],
        frame_id: int,
        timestamp: datetime
    ) -> List[DetectedVehicle]:
        """
        Update vehicle tracks with new frame detections.
        Assigns track_id to each DetectedVehicle.
        """
        if not detected_vehicles:
            # Mark disappeared
            self._cleanup_disappeared(frame_id)
            return []

        if not self.tracked_vehicles:
            # Initialize tracks for all detections
            for veh in detected_vehicles:
                veh.track_id = self.next_track_id
                state = TrackedVehicleState(
                    track_id=self.next_track_id,
                    class_id=veh.class_id,
                    class_name=veh.class_name,
                    current_box=veh.box,
                    confidence=veh.confidence,
                    last_seen_frame=frame_id
                )
                state.update(veh.box, veh.confidence, frame_id, timestamp)
                self.tracked_vehicles[self.next_track_id] = state
                self.next_track_id += 1
            return detected_vehicles

        # Match existing tracks with new detections using IoU matrix
        track_ids = list(self.tracked_vehicles.keys())
        track_boxes = [self.tracked_vehicles[tid].current_box for tid in track_ids]
        det_boxes = [veh.box for veh in detected_vehicles]

        iou_matrix = self._compute_iou_matrix(track_boxes, det_boxes)

        matched_det_indices = set()
        matched_track_indices = set()

        if iou_matrix.size > 0:
            # Greedy matching by max IoU
            while True:
                max_iou = np.max(iou_matrix)
                if max_iou < self.iou_threshold:
                    break
                t_idx, d_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                if t_idx in matched_track_indices or d_idx in matched_det_indices:
                    iou_matrix[t_idx, d_idx] = -1.0
                    continue

                tid = track_ids[t_idx]
                veh = detected_vehicles[d_idx]
                veh.track_id = tid
                self.tracked_vehicles[tid].update(veh.box, veh.confidence, frame_id, timestamp)

                matched_track_indices.add(t_idx)
                matched_det_indices.add(d_idx)
                iou_matrix[t_idx, :] = -1.0
                iou_matrix[:, d_idx] = -1.0

        # Unmatched detections get new track IDs
        for d_idx, veh in enumerate(detected_vehicles):
            if d_idx not in matched_det_indices:
                veh.track_id = self.next_track_id
                state = TrackedVehicleState(
                    track_id=self.next_track_id,
                    class_id=veh.class_id,
                    class_name=veh.class_name,
                    current_box=veh.box,
                    confidence=veh.confidence,
                    last_seen_frame=frame_id
                )
                state.update(veh.box, veh.confidence, frame_id, timestamp)
                self.tracked_vehicles[self.next_track_id] = state
                self.next_track_id += 1

        self._cleanup_disappeared(frame_id)
        return detected_vehicles

    def _compute_iou_matrix(
        self,
        boxesA: List[Tuple[float, float, float, float]],
        boxesB: List[Tuple[float, float, float, float]]
    ) -> np.ndarray:
        """Compute pairwise IoU matrix."""
        matrix = np.zeros((len(boxesA), len(boxesB)), dtype=np.float32)
        for i, boxA in enumerate(boxesA):
            for j, boxB in enumerate(boxesB):
                matrix[i, j] = self._compute_iou(boxA, boxB)
        return matrix

    @staticmethod
    def _compute_iou(boxA: Tuple[float, float, float, float], boxB: Tuple[float, float, float, float]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
        boxBArea = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
        return float(iou)

    def _cleanup_disappeared(self, current_frame_id: int):
        """Purge tracks not seen for max_disappeared frames."""
        to_delete = []
        for tid, state in self.tracked_vehicles.items():
            if (current_frame_id - state.last_seen_frame) > self.max_disappeared:
                to_delete.append(tid)
        for tid in to_delete:
            del self.tracked_vehicles[tid]

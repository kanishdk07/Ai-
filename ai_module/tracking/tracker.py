"""
Multi-Object Vehicle Tracker (ByteTrack / IoU compatible)
Provides persistent object tracking across frames using IoU + Centroid Kalman multi-object tracking algorithm.
Supports ByteTrack two-stage association logic for high-confidence and low-confidence detections.
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
    def vehicle_class(self) -> str:
        return self.class_name

    @property
    def bounding_box(self) -> Tuple[float, float, float, float]:
        return self.current_box

    @property
    def center_x(self) -> float:
        return (self.current_box[0] + self.current_box[2]) / 2.0

    @property
    def center_y(self) -> float:
        return (self.current_box[1] + self.current_box[3]) / 2.0

    @property
    def timestamp(self) -> Optional[datetime]:
        return self.positions[-1][2] if self.positions else None

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
    ByteTrack-compatible Multi-Object Vehicle Tracker.
    Maintains vehicle IDs and computes velocity vectors over time.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_disappeared: int = 15,
        high_conf_thresh: float = 0.45
    ):
        self.iou_threshold = iou_threshold
        self.max_disappeared = max_disappeared
        self.high_conf_thresh = high_conf_thresh
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

        # ByteTrack two-stage matching:
        # Stage 1: High-confidence detections
        high_dets = [v for v in detected_vehicles if v.confidence >= self.high_conf_thresh]
        low_dets = [v for v in detected_vehicles if v.confidence < self.high_conf_thresh]

        track_ids = list(self.tracked_vehicles.keys())
        track_boxes = [self.tracked_vehicles[tid].current_box for tid in track_ids]
        high_det_boxes = [v.box for v in high_dets]

        iou_matrix = self._compute_iou_matrix(track_boxes, high_det_boxes)

        matched_high_det_indices = set()
        matched_track_indices = set()

        if iou_matrix.size > 0:
            while True:
                max_iou = np.max(iou_matrix)
                if max_iou < self.iou_threshold:
                    break
                t_idx, d_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                if t_idx in matched_track_indices or d_idx in matched_high_det_indices:
                    iou_matrix[t_idx, d_idx] = -1.0
                    continue

                tid = track_ids[t_idx]
                veh = high_dets[d_idx]
                veh.track_id = tid
                self.tracked_vehicles[tid].update(veh.box, veh.confidence, frame_id, timestamp)

                matched_track_indices.add(t_idx)
                matched_high_det_indices.add(d_idx)
                iou_matrix[t_idx, :] = -1.0
                iou_matrix[:, d_idx] = -1.0

        # Stage 2: Low-confidence detections for remaining unmatched tracks
        unmatched_track_indices = [i for i in range(len(track_ids)) if i not in matched_track_indices]
        if unmatched_track_indices and low_dets:
            unmatched_track_boxes = [self.tracked_vehicles[track_ids[i]].current_box for i in unmatched_track_indices]
            low_det_boxes = [v.box for v in low_dets]

            low_iou_matrix = self._compute_iou_matrix(unmatched_track_boxes, low_det_boxes)

            matched_low_det_indices = set()
            if low_iou_matrix.size > 0:
                while True:
                    max_iou = np.max(low_iou_matrix)
                    if max_iou < self.iou_threshold:
                        break
                    u_t_idx, l_d_idx = np.unravel_index(np.argmax(low_iou_matrix), low_iou_matrix.shape)
                    if u_t_idx in matched_track_indices or l_d_idx in matched_low_det_indices:
                        low_iou_matrix[u_t_idx, l_d_idx] = -1.0
                        continue

                    orig_t_idx = unmatched_track_indices[u_t_idx]
                    tid = track_ids[orig_t_idx]
                    veh = low_dets[l_d_idx]
                    veh.track_id = tid
                    self.tracked_vehicles[tid].update(veh.box, veh.confidence, frame_id, timestamp)

                    matched_track_indices.add(orig_t_idx)
                    matched_low_det_indices.add(l_d_idx)
                    low_iou_matrix[u_t_idx, :] = -1.0
                    low_iou_matrix[:, l_d_idx] = -1.0

        # Unmatched high-confidence detections get new track IDs
        for d_idx, veh in enumerate(high_dets):
            if d_idx not in matched_high_det_indices and veh.track_id is None:
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

        # Unmatched low-confidence detections that didn't match existing tracks
        for veh in low_dets:
            if veh.track_id is None and len(high_dets) == 0:
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

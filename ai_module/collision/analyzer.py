"""
Vehicle Collision & Movement Analysis Module
Analyzes vehicle trajectory physics over multiple frames to detect potential highway accidents.
Implements temporal candidate creation, confirmation, duplicate suppression, and evidence collection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import math
from typing import List, Dict, Optional, Tuple, Set
import numpy as np

from ai_module.config import settings
from ai_module.detection.yolo_detector import DetectedVehicle
from ai_module.tracking.tracker import MultiObjectVehicleTracker, TrackedVehicleState

logger = logging.getLogger(__name__)


class CollisionStatus:
    NORMAL = "normal"
    CANDIDATE = "potential_candidate"
    CONFIRMED = "confirmed"
    COOLDOWN = "cooldown"


@dataclass
class CollisionEvidence:
    vehicles_involved: List[int]
    max_iou_overlap: float
    max_velocity_drop: float
    min_proximity_px: float
    post_impact_standstill_frames: int
    trajectories_intersect: bool
    evidence_score: float
    raw_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class CollisionEvent:
    event_id: str
    camera_id: str
    created_at: datetime
    status: str  # "potential_candidate", "confirmed"
    confidence_score: float  # 0.0 - 1.0
    evidence: CollisionEvidence
    vehicles: List[DetectedVehicle]
    frame_id: int
    location_verified: bool = False


class CollisionAnalyzer:
    """
    Multi-frame Collision Physics and Temporal Event Detector.
    """

    def __init__(
        self,
        velocity_drop_thresh: float = settings.VELOCITY_DROP_THRESHOLD,
        overlap_thresh: float = settings.OVERLAP_THRESHOLD,
        proximity_thresh_px: float = settings.PROXIMITY_THRESHOLD_PX,
        confirmation_frames: int = settings.CONFIRMATION_FRAMES,
        cooldown_seconds: float = settings.COOLDOWN_SECONDS
    ):
        self.velocity_drop_thresh = velocity_drop_thresh
        self.overlap_thresh = overlap_thresh
        self.proximity_thresh_px = proximity_thresh_px
        self.confirmation_frames = confirmation_frames
        self.cooldown_seconds = cooldown_seconds

        # Candidate tracking state
        self.active_candidates: Dict[str, Dict] = {}  # candidate_key -> candidate data
        self.last_confirmed_event_time: Dict[str, datetime] = {}  # camera_id -> datetime
        self.event_counter = 0

    def analyze_frame(
        self,
        camera_id: str,
        frame_id: int,
        timestamp: datetime,
        detected_vehicles: List[DetectedVehicle],
        tracker: MultiObjectVehicleTracker
    ) -> Tuple[Optional[CollisionEvent], List[CollisionEvent]]:
        """
        Analyze current frame vehicle movements and return (ConfirmedEvent, CandidateEvents).
        """
        active_tracks = tracker.tracked_vehicles

        # Skip analysis if fewer than 2 tracked vehicles or cooldown active
        if self._is_in_cooldown(camera_id, timestamp):
            return None, []

        candidate_pairs = self._detect_collision_indicators(active_tracks)

        confirmed_event: Optional[CollisionEvent] = None
        current_candidates: List[CollisionEvent] = []

        if not candidate_pairs:
            # Decay or reset active candidates
            self._decay_candidates(camera_id)
            return None, []

        for pair_key, evidence in candidate_pairs.items():
            t1_id, t2_id = pair_key
            v1_state = active_tracks.get(t1_id)
            v2_state = active_tracks.get(t2_id)

            if not v1_state or not v2_state:
                continue

            # Event confidence score calculation
            conf_score = self._calculate_event_confidence(evidence)

            # Check candidate persistence over N consecutive frames
            if pair_key not in self.active_candidates:
                self.active_candidates[pair_key] = {
                    "first_seen_frame": frame_id,
                    "first_seen_time": timestamp,
                    "consecutive_frames": 1,
                    "max_confidence": conf_score,
                    "best_evidence": evidence
                }
            else:
                cdata = self.active_candidates[pair_key]
                cdata["consecutive_frames"] += 1
                if conf_score > cdata["max_confidence"]:
                    cdata["max_confidence"] = conf_score
                    cdata["best_evidence"] = evidence

            cand_info = self.active_candidates[pair_key]

            # Generate candidate event object
            pair_vehicles = [
                veh for veh in detected_vehicles
                if veh.track_id in [t1_id, t2_id]
            ]

            self.event_counter += 1
            evt_id = f"ACC-{timestamp.strftime('%Y%m%d%H%M%S')}-{self.event_counter:04d}"

            cand_event = CollisionEvent(
                event_id=evt_id,
                camera_id=camera_id,
                created_at=timestamp,
                status=CollisionStatus.CANDIDATE,
                confidence_score=round(cand_info["max_confidence"], 3),
                evidence=cand_info["best_evidence"],
                vehicles=pair_vehicles if pair_vehicles else detected_vehicles,
                frame_id=frame_id
            )
            current_candidates.append(cand_event)

            # Check if confirmed (persisted across required temporal confirmation frames)
            if cand_info["consecutive_frames"] >= self.confirmation_frames and cand_info["max_confidence"] >= 0.45:
                cand_event.status = CollisionStatus.CONFIRMED
                confirmed_event = cand_event
                self.last_confirmed_event_time[camera_id] = timestamp

                # Clean candidate once confirmed
                del self.active_candidates[pair_key]
                logger.info(
                    f"🚨 [ACCIDENT CONFIRMED] Event {evt_id} on Camera [{camera_id}] (Conf: {cand_event.confidence_score})"
                )
                break

        return confirmed_event, current_candidates

    def _is_in_cooldown(self, camera_id: str, timestamp: datetime) -> bool:
        """Check if camera is in cooldown window after a recent confirmed collision."""
        if camera_id in self.last_confirmed_event_time:
            last_t = self.last_confirmed_event_time[camera_id]
            if (timestamp - last_t).total_seconds() < self.cooldown_seconds:
                return True
        return False

    def _detect_collision_indicators(
        self,
        tracks: Dict[int, TrackedVehicleState]
    ) -> Dict[Tuple[int, int], CollisionEvidence]:
        """
        Examine pairwise vehicle states for collision physics indicators.
        """
        indicators: Dict[Tuple[int, int], CollisionEvidence] = {}
        tids = list(tracks.keys())

        for i in range(len(tids)):
            for j in range(i + 1, len(tids)):
                tid1, tid2 = tids[i], tids[j]
                v1, v2 = tracks[tid1], tracks[tid2]

                # 1. Bounding box Intersection over Min Area (Overlap)
                iou_overlap = self._compute_intersection_over_min(v1.current_box, v2.current_box)

                # 2. Distance between vehicle centroids
                c1 = ((v1.current_box[0] + v1.current_box[2]) / 2.0, (v1.current_box[1] + v1.current_box[3]) / 2.0)
                c2 = ((v2.current_box[0] + v2.current_box[2]) / 2.0, (v1.current_box[1] + v2.current_box[3]) / 2.0)
                dist_px = float(np.hypot(c1[0] - c2[0], c1[1] - c2[1]))

                # 3. Sudden Velocity Drops (Deceleration / Stop)
                drop1 = self._calculate_velocity_drop(v1)
                drop2 = self._calculate_velocity_drop(v2)
                max_vel_drop = max(drop1, drop2)

                # 4. Trajectory Convergence / Intersection
                trajectories_intersect = self._check_trajectory_intersection(v1, v2)

                # 5. Post-Impact Standstill
                standstill_frames = min(self._count_standstill_frames(v1), self._count_standstill_frames(v2))

                # Check if indicators exceed candidate threshold
                is_candidate = (
                    (iou_overlap >= self.overlap_thresh) or
                    (max_vel_drop >= self.velocity_drop_thresh and dist_px <= self.proximity_thresh_px * 2.0) or
                    (trajectories_intersect and dist_px <= self.proximity_thresh_px and max_vel_drop > 0.3)
                )

                if is_candidate:
                    pair_key = (min(tid1, tid2), max(tid1, tid2))

                    evidence_score = (
                        (iou_overlap * 0.35) +
                        (max_vel_drop * 0.35) +
                        (1.0 - min(1.0, dist_px / max(1.0, self.proximity_thresh_px * 2))) * 0.20 +
                        (1.0 if trajectories_intersect else 0.0) * 0.10
                    )

                    evidence = CollisionEvidence(
                        vehicles_involved=[tid1, tid2],
                        max_iou_overlap=round(float(iou_overlap), 3),
                        max_velocity_drop=round(float(max_vel_drop), 3),
                        min_proximity_px=round(float(dist_px), 2),
                        post_impact_standstill_frames=standstill_frames,
                        trajectories_intersect=trajectories_intersect,
                        evidence_score=round(float(evidence_score), 3),
                        raw_metrics={
                            "dist_px": round(dist_px, 2),
                            "drop_v1": round(drop1, 3),
                            "drop_v2": round(drop2, 3),
                            "speed_v1": round(v1.current_speed, 2),
                            "speed_v2": round(v2.current_speed, 2)
                        }
                    )
                    indicators[pair_key] = evidence

        return indicators

    @staticmethod
    def _compute_intersection_over_min(boxA, boxB) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        areaA = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
        areaB = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])

        minArea = min(areaA, areaB)
        if minArea <= 0:
            return 0.0
        return interArea / float(minArea)

    @staticmethod
    def _calculate_velocity_drop(vehicle: TrackedVehicleState) -> float:
        """Calculate relative drop in speed compared to recent peak speed."""
        if len(vehicle.speed_history) < 5:
            return 0.0
        past_speeds = vehicle.speed_history[:-2]
        max_past_speed = float(np.max(past_speeds)) if past_speeds else 0.0
        if max_past_speed < 5.0:  # Ignore stationary/crawling vehicles
            return 0.0

        current_speed = vehicle.current_speed
        speed_drop = (max_past_speed - current_speed) / max_past_speed
        return max(0.0, float(speed_drop))

    @staticmethod
    def _check_trajectory_intersection(v1: TrackedVehicleState, v2: TrackedVehicleState) -> bool:
        """Check if motion vectors of v1 and v2 cross."""
        if len(v1.velocities) < 2 or len(v2.velocities) < 2:
            return False
        vx1, vy1 = v1.velocities[-1]
        vx2, vy2 = v2.velocities[-1]
        # Cross product of velocity vectors
        cross_prod = abs(vx1 * vy2 - vy1 * vx2)
        dot_prod = vx1 * vx2 + vy1 * vy2
        # Head-on or crossing trajectory indicator
        return cross_prod > 50.0 or dot_prod < -100.0

    @staticmethod
    def _count_standstill_frames(vehicle: TrackedVehicleState) -> int:
        """Count consecutive recent frames where vehicle speed is near zero."""
        count = 0
        for spd in reversed(vehicle.speed_history):
            if spd < 3.0:
                count += 1
            else:
                break
        return count

    @staticmethod
    def _calculate_event_confidence(evidence: CollisionEvidence) -> float:
        """Calculate overall collision confidence score (0.0 to 1.0)."""
        score = evidence.evidence_score
        # Boost confidence if post-impact standstill observed
        if evidence.post_impact_standstill_frames >= 3:
            score += 0.15
        return min(1.0, max(0.0, score))

    def _decay_candidates(self, camera_id: str):
        """Remove stale candidates if not seen in recent frames."""
        stale = [k for k in self.active_candidates.keys()]
        for k in stale:
            self.active_candidates[k]["consecutive_frames"] -= 1
            if self.active_candidates[k]["consecutive_frames"] <= 0:
                del self.active_candidates[k]

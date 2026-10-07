"""
Accident Severity Classification Module
Estimates collision severity (High, Medium, Low) based on temporal visual features and impact physical metrics.
Includes review-required flags, confidence scoring, and strict safety disclaimers.
"""

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Dict, Any, Tuple

from ai_module.collision.analyzer import CollisionEvent, CollisionEvidence

logger = logging.getLogger(__name__)


class SeverityCategory(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SeverityResult:
    severity: SeverityCategory
    confidence_score: float  # 0.0 to 1.0
    review_required: bool
    reasons: list
    disclaimer: str = (
        "Notice: AI severity classification is strictly based on visual motion dynamics. "
        "It does NOT estimate actual human injuries, fatalities, or medical condition."
    )


class SeverityClassifier:
    """
    Temporal Feature-Based Accident Severity Estimator.
    """

    def __init__(
        self,
        high_threshold: float = 0.75,
        medium_threshold: float = 0.50
    ):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold

    def classify(self, event: CollisionEvent) -> SeverityResult:
        """
        Classify the collision event into High, Medium, or Low severity.
        Returns SeverityResult with confidence score and review flag.
        """
        evidence = event.evidence
        reasons = []
        review_required = False

        # Extract features
        iou = evidence.max_iou_overlap
        vel_drop = evidence.max_velocity_drop
        dist_px = evidence.min_proximity_px
        standstill = evidence.post_impact_standstill_frames
        intersect = evidence.trajectories_intersect
        num_vehicles = len(event.vehicles)

        # 1. Calculate raw severity feature score
        severity_score = 0.0

        # Overlap score contribution
        if iou > 0.40:
            severity_score += 0.35
            reasons.append(f"Significant vehicle bounding box overlap (IoU: {iou:.2f})")
        elif iou > 0.20:
            severity_score += 0.20
            reasons.append(f"Moderate vehicle bounding box overlap (IoU: {iou:.2f})")
        else:
            severity_score += 0.10

        # Velocity drop contribution
        if vel_drop > 0.70:
            severity_score += 0.35
            reasons.append(f"Severe abrupt deceleration drop ({vel_drop * 100:.1f}%)")
        elif vel_drop > 0.45:
            severity_score += 0.20
            reasons.append(f"Noticeable speed reduction drop ({vel_drop * 100:.1f}%)")
        else:
            severity_score += 0.10

        # Multi-vehicle involvement
        if num_vehicles >= 3:
            severity_score += 0.15
            reasons.append(f"Multi-vehicle crash involvement ({num_vehicles} vehicles)")

        # Post-impact immobilization
        if standstill >= 5:
            severity_score += 0.15
            reasons.append(f"Sustained post-impact vehicle immobilization ({standstill} frames)")

        # Trajectory crossing
        if intersect:
            severity_score += 0.10
            reasons.append("Intersecting vehicle trajectories confirmed")

        severity_score = min(1.0, max(0.0, severity_score))

        # 2. Determine Category
        if severity_score >= self.high_threshold:
            category = SeverityCategory.HIGH
        elif severity_score >= self.medium_threshold:
            category = SeverityCategory.MEDIUM
        else:
            category = SeverityCategory.LOW

        # 3. Handle Uncertainty & Human Review Trigger
        # If confidence score of event is low or metrics conflict, mark review_required
        confidence = round(float(event.confidence_score * 0.5 + severity_score * 0.5), 3)

        if confidence < 0.60 or iou < 0.15 or (category == SeverityCategory.HIGH and num_vehicles < 2):
            review_required = True
            reasons.append("Evidence parameters require operator human review")

        logger.info(
            f"Event [{event.event_id}] classified as Severity={category.value.upper()} "
            f"(Score: {severity_score:.2f}, Conf: {confidence}, ReviewRequired: {review_required})"
        )

        return SeverityResult(
            severity=category,
            confidence_score=confidence,
            review_required=review_required,
            reasons=reasons
        )

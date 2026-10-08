"""
Accident Severity & Risk Classification Module
Estimates collision severity (HIGH, MEDIUM, LOW, UNCERTAIN) based on temporal visual features and impact physical metrics.
Includes review-required flags, confidence scoring, pluggable classifier interface, and strict safety disclaimers.
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Dict, Any, List, Tuple, Optional

from ai_module.collision.analyzer import CollisionEvent, CollisionEvidence
from ai_module.config import settings

logger = logging.getLogger(__name__)


class SeverityCategory(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNCERTAIN = "UNCERTAIN"

    @classmethod
    def _missing_(cls, value):
        """Case-insensitive enum lookup fallback."""
        if isinstance(value, str):
            val_upper = value.upper()
            for member in cls:
                if member.value == val_upper or member.name == val_upper:
                    return member
        return cls.UNCERTAIN


@dataclass
class SeverityResult:
    severity: SeverityCategory
    confidence_score: float  # 0.0 to 1.0
    review_required: bool
    reasons: List[str] = field(default_factory=list)
    disclaimer: str = (
        "Notice: AI severity classification is strictly a visual accident-risk/severity estimate based on vehicle dynamics. "
        "It does NOT assess actual human injuries, fatalities, or medical condition."
    )

    @property
    def risk_level(self) -> str:
        return self.severity.value.upper()

    @property
    def risk_confidence(self) -> float:
        return self.confidence_score


class SeverityClassifier:
    """
    Temporal Feature-Based Accident Risk & Severity Estimator.
    Provides a modular interface for rule-based heuristics and trained classifier models.

    Note: Currently utilizes temporal movement heuristics validated on highway traffic scenarios.
    A dedicated trained deep learning model can be plugged into `classify()` without changing the pipeline.
    """

    def __init__(
        self,
        high_threshold: float = settings.RISK_HIGH_THRESHOLD,
        medium_threshold: float = settings.RISK_MEDIUM_THRESHOLD,
        low_threshold: float = settings.RISK_LOW_THRESHOLD
    ):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.low_threshold = low_threshold

    def classify(self, event: CollisionEvent) -> SeverityResult:
        """
        Classify the collision event into HIGH, MEDIUM, LOW, or UNCERTAIN.
        Returns SeverityResult with confidence score and review_required flag.
        """
        evidence = event.evidence
        reasons: List[str] = []
        review_required = False

        # Extract collision dynamics features
        iou = evidence.max_iou_overlap
        vel_drop = evidence.max_velocity_drop
        dist_px = evidence.min_proximity_px
        standstill = evidence.post_impact_standstill_frames
        intersect = evidence.trajectories_intersect
        num_vehicles = len(event.vehicles)
        event_conf = event.confidence_score

        # 1. Check UNCERTAIN Conditions
        # UNCERTAIN is assigned when evidence is ambiguous, low confidence, heavily occluded, or insufficient
        is_uncertain = (
            event_conf < 0.40 or
            (iou < 0.10 and vel_drop < 0.30) or
            (num_vehicles < 2 and vel_drop < 0.50) or
            event.status == "potential_candidate"
        )

        if is_uncertain:
            reasons.append("Visual evidence is ambiguous or confidence threshold is insufficient")
            reasons.append("Collision candidate marked UNCERTAIN requiring operator review")
            review_required = True
            confidence = round(float(event_conf * 0.7), 3)
            return SeverityResult(
                severity=SeverityCategory.UNCERTAIN,
                confidence_score=confidence,
                review_required=True,
                reasons=reasons
            )

        # 2. Calculate raw severity feature score (0.0 to 1.0)
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

        # 3. Categorize into HIGH, MEDIUM, LOW
        if severity_score >= self.high_threshold:
            category = SeverityCategory.HIGH
        elif severity_score >= self.medium_threshold:
            category = SeverityCategory.MEDIUM
        else:
            category = SeverityCategory.LOW

        # 4. Handle Uncertainty & Human Review Trigger
        confidence = round(float(event_conf * 0.4 + severity_score * 0.6), 3)

        if confidence < 0.60 or iou < 0.15 or (category == SeverityCategory.HIGH and num_vehicles < 2):
            review_required = True
            reasons.append("Evidence parameters require operator human review")

        logger.info(
            f"Event [{event.event_id}] classified as RiskLevel={category.value} "
            f"(Score: {severity_score:.2f}, Conf: {confidence}, ReviewRequired: {review_required})"
        )

        return SeverityResult(
            severity=category,
            confidence_score=confidence,
            review_required=review_required,
            reasons=reasons
        )

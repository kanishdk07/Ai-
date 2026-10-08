"""
Unit Tests for Severity Classifier and Evidence Capture Service
"""

from datetime import datetime, timezone
import numpy as np
import pytest
from pathlib import Path

from ai_module.detection import DetectedVehicle
from ai_module.collision import CollisionEvent, CollisionEvidence, CollisionStatus
from ai_module.severity import SeverityClassifier, SeverityCategory
from ai_module.capture import EvidenceCaptureService


def test_severity_classification_high():
    classifier = SeverityClassifier()
    now = datetime.now(timezone.utc)

    # High severity evidence: severe overlap (0.50), high velocity drop (0.80), 3 vehicles
    evidence = CollisionEvidence(
        vehicles_involved=[1, 2, 3],
        max_iou_overlap=0.50,
        max_velocity_drop=0.80,
        min_proximity_px=10.0,
        post_impact_standstill_frames=10,
        trajectories_intersect=True,
        evidence_score=0.85
    )

    vehicles = [
        DetectedVehicle(box=(10, 10, 50, 50), confidence=0.9, class_id=2, class_name="car", track_id=1),
        DetectedVehicle(box=(20, 20, 60, 60), confidence=0.9, class_id=7, class_name="truck", track_id=2),
        DetectedVehicle(box=(30, 30, 70, 70), confidence=0.9, class_id=2, class_name="car", track_id=3),
    ]

    event = CollisionEvent(
        event_id="ACC-TEST-HIGH",
        camera_id="CAM-01",
        created_at=now,
        status=CollisionStatus.CONFIRMED,
        confidence_score=0.90,
        evidence=evidence,
        vehicles=vehicles,
        frame_id=10
    )

    res = classifier.classify(event)
    assert res.severity == SeverityCategory.HIGH
    assert res.confidence_score >= 0.70
    assert "Notice" in res.disclaimer


def test_evidence_capture_service(tmp_path):
    capture_svc = EvidenceCaptureService(storage_dir=tmp_path)
    now = datetime.now(timezone.utc)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    evidence = CollisionEvidence(
        vehicles_involved=[1, 2],
        max_iou_overlap=0.3,
        max_velocity_drop=0.5,
        min_proximity_px=15.0,
        post_impact_standstill_frames=5,
        trajectories_intersect=True,
        evidence_score=0.65
    )

    event = CollisionEvent(
        event_id="ACC-TEST-CAPTURE",
        camera_id="CAM-CAP-01",
        created_at=now,
        status=CollisionStatus.CONFIRMED,
        confidence_score=0.75,
        evidence=evidence,
        vehicles=[],
        frame_id=5
    )

    classifier = SeverityClassifier()
    sev_res = classifier.classify(event)

    pkg = capture_svc.capture_evidence(dummy_frame, event, sev_res)

    assert pkg.clean_image_path.exists()
    assert pkg.annotated_image_path.exists()
    assert pkg.event_id == "ACC-TEST-CAPTURE"
    assert "/static/evidence/" in pkg.clean_image_url

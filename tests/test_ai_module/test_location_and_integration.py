"""
Unit Tests for Location Registry and Backend Integration Client
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock

from ai_module.location import LocationRegistry, LocationData
from ai_module.integration import BackendIntegrationClient
from ai_module.collision import CollisionEvent, CollisionEvidence, CollisionStatus
from ai_module.severity import SeverityClassifier
from ai_module.capture import EvidencePackage


def test_location_registry_registered_and_mobile():
    reg = LocationRegistry()

    # Register static camera
    reg.register_camera_location("CAM-SYS-10", 37.7749, -122.4194, "Highway 101 KM 42")

    loc1 = reg.resolve_location("CAM-SYS-10")
    assert loc1.is_verified is True
    assert loc1.latitude == 37.7749
    assert loc1.source == "registered_camera"

    # Mobile GPS override
    mobile_gps = {"latitude": 34.0522, "longitude": -118.2437}
    loc2 = reg.resolve_location("CAM-SYS-10", override_gps=mobile_gps)
    assert loc2.is_verified is True
    assert loc2.latitude == 34.0522
    assert loc2.source == "mobile_gps"

    # Missing location fallback
    loc3 = reg.resolve_location("CAM-UNKNOWN")
    assert loc3.is_verified is False
    assert loc3.latitude is None
    assert loc3.source == "unverified"


def test_backend_client_offline_buffering(tmp_path):
    buffer_file = tmp_path / "offline.json"
    client = BackendIntegrationClient(
        backend_url="http://invalid-localhost:9999",  # Unreachable port to force offline buffering
        offline_buffer_file=buffer_file,
        max_retries=1,
        timeout=0.1
    )

    now = datetime.now(timezone.utc)
    evidence = CollisionEvidence(
        vehicles_involved=[1],
        max_iou_overlap=0.4,
        max_velocity_drop=0.6,
        min_proximity_px=10.0,
        post_impact_standstill_frames=5,
        trajectories_intersect=True,
        evidence_score=0.70
    )

    event = CollisionEvent(
        event_id="ACC-OFFLINE-01",
        camera_id="CAM-OFFLINE-01",
        created_at=now,
        status=CollisionStatus.CONFIRMED,
        confidence_score=0.80,
        evidence=evidence,
        vehicles=[],
        frame_id=1
    )

    classifier = SeverityClassifier()
    sev_res = classifier.classify(event)

    ev_pkg = EvidencePackage(
        event_id="ACC-OFFLINE-01",
        camera_id="CAM-OFFLINE-01",
        timestamp=now,
        clean_image_path=tmp_path / "clean.jpg",
        annotated_image_path=tmp_path / "ann.jpg",
        clean_image_url="/static/evidence/clean.jpg",
        annotated_image_url="/static/evidence/ann.jpg",
        pre_event_frame_count=30,
        post_event_frame_count=0,
        metadata={}
    )

    loc = LocationData(latitude=37.77, longitude=-122.41, location_description="Test", is_verified=True, source="mobile")

    success = client.submit_incident(event, sev_res, ev_pkg, loc)

    # Should report False (network down) but store payload in offline buffer file
    assert success is False
    assert buffer_file.exists()

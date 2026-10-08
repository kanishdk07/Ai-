"""
AI Accident Detection Pipeline Orchestrator
Integrates camera input streams, YOLO11 detection, multi-vehicle tracking, multi-frame collision physics analysis,
severity classification, evidence image capture, GPS location mapping, and FastAPI backend reporting.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from ai_module.config import settings
from ai_module.camera.manager import CameraInputManager
from ai_module.camera.base import FrameData, CameraStatus
from ai_module.detection.yolo_detector import YOLO11Detector
from ai_module.tracking.tracker import MultiObjectVehicleTracker
from ai_module.collision.analyzer import CollisionAnalyzer, CollisionEvent, CollisionStatus
from ai_module.severity.classifier import SeverityClassifier, SeverityResult
from ai_module.capture.capture_service import EvidenceCaptureService, EvidencePackage
from ai_module.location.location_service import LocationRegistry, LocationData
from ai_module.integration.backend_client import BackendIntegrationClient
from ai_module.evaluation.evaluator import PerformanceMonitor, PerformanceReport

logger = logging.getLogger(__name__)


class AccidentDetectionPipeline:
    """
    Main AI Orchestrator Pipeline.
    """

    def __init__(
        self,
        camera_manager: Optional[CameraInputManager] = None,
        detector: Optional[YOLO11Detector] = None,
        tracker: Optional[MultiObjectVehicleTracker] = None,
        analyzer: Optional[CollisionAnalyzer] = None,
        severity_classifier: Optional[SeverityClassifier] = None,
        capture_service: Optional[EvidenceCaptureService] = None,
        location_registry: Optional[LocationRegistry] = None,
        backend_client: Optional[BackendIntegrationClient] = None,
        enable_backend_submission: bool = True
    ):
        self.camera_manager = camera_manager or CameraInputManager()
        self.detector = detector or YOLO11Detector()
        self.tracker = tracker or MultiObjectVehicleTracker()
        self.analyzer = analyzer or CollisionAnalyzer()
        self.severity_classifier = severity_classifier or SeverityClassifier()
        self.capture_service = capture_service or EvidenceCaptureService()
        self.location_registry = location_registry or LocationRegistry()
        self.backend_client = backend_client or BackendIntegrationClient() if enable_backend_submission else None
        self.monitor = PerformanceMonitor()

        self.enable_backend = enable_backend_submission
        self.is_running = False
        self.detected_incidents: List[CollisionEvent] = []

    def process_frame(
        self,
        frame_data: FrameData,
        override_gps: Optional[Dict[str, float]] = None
    ) -> Tuple[Optional[CollisionEvent], List[CollisionEvent], np.ndarray]:
        """
        Process a single frame through the complete AI accident detection pipeline.
        Returns (ConfirmedEvent, CandidateEvents, AnnotatedFrame).
        """
        t0 = time.time()
        cam_id = frame_data.camera_id
        frame_id = frame_data.frame_id
        timestamp = frame_data.timestamp
        image = frame_data.image

        # 1. Update Pre-event ring buffer
        self.capture_service.add_frame_to_buffer(cam_id, frame_data)

        # 2. Vehicle Detection (YOLO11)
        det_result = self.detector.detect(
            image=image,
            frame_id=frame_id,
            timestamp=timestamp,
            camera_id=cam_id
        )

        # 3. Multi-object Vehicle Tracking
        tracked_vehicles = self.tracker.update(
            detected_vehicles=det_result.vehicles,
            frame_id=frame_id,
            timestamp=timestamp
        )

        # 4. Multi-frame Collision Physics Analysis
        confirmed_event, candidate_events = self.analyzer.analyze_frame(
            camera_id=cam_id,
            frame_id=frame_id,
            timestamp=timestamp,
            detected_vehicles=tracked_vehicles,
            tracker=self.tracker
        )

        t_end = time.time()
        total_dt_ms = (t_end - t0) * 1000.0
        self.monitor.record_frame(det_result.inference_time_ms, total_dt_ms)

        annotated_preview = image

        # 5. Handle Confirmed Accident Event
        if confirmed_event is not None:
            self.detected_incidents.append(confirmed_event)

            # Classify Accident Severity
            severity_res = self.severity_classifier.classify(confirmed_event)

            # Capture Evidence Package & Annotated Preview
            evidence_pkg = self.capture_service.capture_evidence(
                current_frame=image,
                event=confirmed_event,
                severity_result=severity_res,
                extra_metadata=frame_data.metadata
            )
            annotated_preview = cv2.imread(str(evidence_pkg.annotated_image_path)) if evidence_pkg.annotated_image_path.exists() else image

            # Resolve Spatial GPS Location
            gps_meta = override_gps or frame_data.metadata.get("gps")
            loc_data = self.location_registry.resolve_location(cam_id, gps_meta)

            # Submit to FastAPI Backend Client
            if self.enable_backend and self.backend_client:
                self.backend_client.submit_incident(
                    event=confirmed_event,
                    severity_result=severity_res,
                    evidence=evidence_pkg,
                    location=loc_data
                )

        return confirmed_event, candidate_events, annotated_preview

    def run_stream_loop(self, camera_id: str, max_frames: Optional[int] = None):
        """
        Synchronous loop to process a stream continuously.
        """
        self.is_running = True
        logger.info(f"Starting pipeline stream loop for Camera [{camera_id}]...")

        processed = 0
        try:
            while self.is_running:
                frame_data = self.camera_manager.read_frame(camera_id)
                if frame_data is None:
                    time.sleep(0.01)
                    continue

                confirmed, candidates, preview = self.process_frame(frame_data)

                processed += 1
                if max_frames and processed >= max_frames:
                    break
        except KeyboardInterrupt:
            logger.info("Stream loop interrupted by user.")
        finally:
            self.is_running = False
            logger.info(f"Stream loop finished. Processed {processed} frames.")

    def get_performance_report(self) -> PerformanceReport:
        """Get pipeline hardware and latency report."""
        return self.monitor.generate_report()

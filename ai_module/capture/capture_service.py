"""
Accident Image Capture & Evidence Storage Service
Manages pre/post frame ring buffers, clean evidence preservation, annotated preview generation, and secure image saving.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Deque
import cv2
import numpy as np

from ai_module.config import settings
from ai_module.camera.base import FrameData
from ai_module.collision.analyzer import CollisionEvent
from ai_module.severity.classifier import SeverityResult

logger = logging.getLogger(__name__)


@dataclass
class EvidencePackage:
    event_id: str
    camera_id: str
    timestamp: datetime
    clean_image_path: Path
    annotated_image_path: Path
    clean_image_url: str
    annotated_image_url: str
    pre_event_frame_count: int
    post_event_frame_count: int
    metadata: Dict[str, str]


class FrameRingBuffer:
    """
    Rolling ring buffer for pre-event and post-event video frame capture.
    """

    def __init__(self, capacity: int = 30):
        self.buffer: Deque[FrameData] = deque(maxlen=capacity)

    def add(self, frame_data: FrameData):
        self.buffer.append(frame_data)

    def get_frames(self) -> List[FrameData]:
        return list(self.buffer)

    def clear(self):
        self.buffer.clear()


class EvidenceCaptureService:
    """
    Preserves clean evidence frames and generates dashboard visual previews.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or settings.STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.ring_buffers: Dict[str, FrameRingBuffer] = {}

    def get_ring_buffer(self, camera_id: str) -> FrameRingBuffer:
        if camera_id not in self.ring_buffers:
            self.ring_buffers[camera_id] = FrameRingBuffer(capacity=settings.PRE_EVENT_BUFFER_FRAMES)
        return self.ring_buffers[camera_id]

    def add_frame_to_buffer(self, camera_id: str, frame_data: FrameData):
        buf = self.get_ring_buffer(camera_id)
        buf.add(frame_data)

    def capture_evidence(
        self,
        current_frame: np.ndarray,
        event: CollisionEvent,
        severity_result: SeverityResult,
        extra_metadata: Optional[dict] = None
    ) -> EvidencePackage:
        """
        Preserve un-overlayed clean evidence image and create annotated preview image.
        """
        evt_id = event.event_id
        cam_id = event.camera_id
        ts = event.created_at

        clean_filename = f"{evt_id}_clean.jpg"
        annotated_filename = f"{evt_id}_annotated.jpg"

        clean_path = self.storage_dir / clean_filename
        annotated_path = self.storage_dir / annotated_filename

        # 1. Save pristine clean original frame
        cv2.imwrite(str(clean_path), current_frame)

        # 2. Draw annotated preview frame for dashboard
        annotated_frame = self._render_annotated_preview(
            current_frame=current_frame,
            event=event,
            severity_result=severity_result
        )
        cv2.imwrite(str(annotated_path), annotated_frame)

        # Get ring buffer frame count
        ring_buf = self.get_ring_buffer(cam_id)
        pre_count = len(ring_buf.get_frames())

        clean_url = f"/static/evidence/{clean_filename}"
        annotated_url = f"/static/evidence/{annotated_filename}"

        meta = {
            "event_id": evt_id,
            "camera_id": cam_id,
            "timestamp": ts.isoformat(),
            "severity": severity_result.severity.value,
            "confidence": str(severity_result.confidence_score),
            "review_required": str(severity_result.review_required)
        }
        if extra_metadata:
            meta.update(extra_metadata)

        logger.info(f"Captured evidence package for event [{evt_id}] saved to {clean_path}")

        return EvidencePackage(
            event_id=evt_id,
            camera_id=cam_id,
            timestamp=ts,
            clean_image_path=clean_path,
            annotated_image_path=annotated_path,
            clean_image_url=clean_url,
            annotated_image_url=annotated_url,
            pre_event_frame_count=pre_count,
            post_event_frame_count=0,
            metadata=meta
        )

    def _render_annotated_preview(
        self,
        current_frame: np.ndarray,
        event: CollisionEvent,
        severity_result: SeverityResult
    ) -> np.ndarray:
        """Render annotated visualization preview with bounding boxes, badges, and metadata overlay."""
        img = current_frame.copy()
        h, w = img.shape[:2]

        # Draw vehicle bounding boxes
        for veh in event.vehicles:
            x1, y1, x2, y2 = map(int, veh.box)
            tid_str = f"ID:{veh.track_id}" if veh.track_id else ""
            label = f"{veh.class_name.upper()} {tid_str} ({veh.confidence:.2f})"

            color = (0, 165, 255) if veh.track_id in event.evidence.vehicles_involved else (0, 255, 0)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, label, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Top Overlay Banner
        sev_val = severity_result.severity.value.upper()
        if sev_val == "HIGH":
            banner_color = (0, 0, 220)  # Red
        elif sev_val == "MEDIUM":
            banner_color = (0, 140, 255)  # Orange
        else:
            banner_color = (0, 200, 200)  # Yellow

        # Draw top banner box
        cv2.rectangle(img, (0, 0), (w, 50), (30, 30, 30), -1)
        cv2.rectangle(img, (0, 0), (180, 50), banner_color, -1)

        banner_text = f"ACCIDENT: {sev_val}"
        cv2.putText(img, banner_text, (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        info_text = f"ID: {event.event_id} | Cam: {event.camera_id} | Conf: {severity_result.confidence_score:.2f}"
        if severity_result.review_required:
            info_text += " [REVIEW REQUIRED]"
        cv2.putText(img, info_text, (195, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        return img

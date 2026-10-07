"""
Backend API Integration Client
Submits detected accident events to the FastAPI backend with idempotency, exponential backoff retry,
and offline event buffering during network interruptions.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests

from ai_module.config import settings
from ai_module.collision.analyzer import CollisionEvent
from ai_module.severity.classifier import SeverityResult
from ai_module.capture.capture_service import EvidencePackage
from ai_module.location.location_service import LocationData

logger = logging.getLogger(__name__)


class BackendIntegrationClient:
    """
    HTTP Client for submitting incidents to the FastAPI Backend.
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        incident_endpoint: Optional[str] = None,
        offline_buffer_file: Optional[Path] = None,
        max_retries: int = settings.MAX_RETRIES,
        timeout: float = settings.REQUEST_TIMEOUT
    ):
        self.backend_url = (backend_url or settings.BACKEND_API_URL).rstrip("/")
        self.endpoint = incident_endpoint or settings.INCIDENT_ENDPOINT
        self.full_url = f"{self.backend_url}{self.endpoint}"
        self.offline_buffer_file = offline_buffer_file or settings.OFFLINE_BUFFER_FILE
        self.max_retries = max_retries
        self.timeout = timeout

        self.session = requests.Session()
        self.offline_buffer_file.parent.mkdir(parents=True, exist_ok=True)
        self._flush_offline_buffer()

    def submit_incident(
        self,
        event: CollisionEvent,
        severity_result: SeverityResult,
        evidence: EvidencePackage,
        location: LocationData
    ) -> bool:
        """
        Build payload matching Backend `IncidentCreate` schema and submit to FastAPI API.
        """
        idempotency_key = f"IDEM-{event.camera_id}-{event.event_id}"

        # Vehicle breakdown structure matching vehicle_info JSON schema
        vehicle_info = {
            "vehicle_count": len(event.vehicles),
            "breakdown": {},
            "tracked_vehicles": []
        }
        for veh in event.vehicles:
            c_name = veh.class_name
            vehicle_info["breakdown"][c_name] = vehicle_info["breakdown"].get(c_name, 0) + 1
            vehicle_info["tracked_vehicles"].append({
                "track_id": veh.track_id,
                "class_name": veh.class_name,
                "confidence": round(float(veh.confidence), 3),
                "box": [round(float(b), 2) for b in veh.box]
            })

        # Structured AI Event Data
        ai_event_data = {
            "event_id": event.event_id,
            "status": event.status,
            "camera_id": event.camera_id,
            "review_required": severity_result.review_required,
            "severity_reasons": severity_result.reasons,
            "annotated_image_url": evidence.annotated_image_url,
            "evidence_metrics": event.evidence.raw_metrics,
            "location_verified": location.is_verified,
            "location_source": location.source
        }

        # FastAPI IncidentCreate Payload Contract
        payload: Dict[str, Any] = {
            "incident_id": event.event_id,
            "camera_external_id": event.camera_id,
            "detected_at": event.created_at.isoformat(),
            "accident_detected": True,
            "severity": severity_result.severity.value,
            "confidence_score": float(severity_result.confidence_score),
            "latitude": location.latitude,
            "longitude": location.longitude,
            "location_description": location.location_description,
            "accident_image_url": evidence.clean_image_url,
            "vehicle_count": len(event.vehicles),
            "vehicle_info": vehicle_info,
            "ai_event_data": ai_event_data,
            "idempotency_key": idempotency_key
        }

        # Try submitting with retries
        success = self._post_with_retry(payload)
        if not success:
            logger.warning(f"Network error submitting event [{event.event_id}]. Storing in offline buffer.")
            self._save_to_offline_buffer(payload)

        # Attempt to flush any previously buffered events if network recovered
        self._flush_offline_buffer()
        return success

    def _post_with_retry(self, payload: Dict[str, Any]) -> bool:
        """Post payload to FastAPI backend with exponential backoff retries."""
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = {"Content-Type": "application/json"}
                response = self.session.post(
                    self.full_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    logger.info(
                        f"Successfully submitted incident [{payload['incident_id']}] to backend "
                        f"(HTTP {response.status_code})"
                    )
                    return True
                elif response.status_code == 409:  # Duplicate / Idempotent already created
                    logger.info(f"Incident [{payload['incident_id']}] already processed by backend (Duplicate/409).")
                    return True
                else:
                    logger.warning(
                        f"Backend API error response HTTP {response.status_code} "
                        f"(Attempt {attempt}/{self.max_retries}): {response.text[:200]}"
                    )
            except requests.RequestException as e:
                logger.warning(f"Connection failure to {self.full_url} (Attempt {attempt}/{self.max_retries}): {e}")

            if attempt < self.max_retries:
                time.sleep(2.0 ** attempt)  # Exponential backoff (2s, 4s, 8s)

        return False

    def _save_to_offline_buffer(self, payload: Dict[str, Any]):
        """Save payload to disk buffer during backend network outage."""
        buffered_events = []
        if self.offline_buffer_file.exists():
            try:
                with open(self.offline_buffer_file, "r", encoding="utf-8") as f:
                    buffered_events = json.load(f)
            except Exception:
                buffered_events = []

        buffered_events.append(payload)

        try:
            with open(self.offline_buffer_file, "w", encoding="utf-8") as f:
                json.dump(buffered_events, f, indent=2)
            logger.info(f"Saved payload to offline buffer ({len(buffered_events)} items total).")
        except Exception as e:
            logger.error(f"Failed to write to offline buffer file: {e}")

    def _flush_offline_buffer(self):
        """Attempt to flush buffered offline events when backend is reachable."""
        if not self.offline_buffer_file.exists():
            return

        try:
            with open(self.offline_buffer_file, "r", encoding="utf-8") as f:
                events = json.load(f)
        except Exception:
            return

        if not events:
            return

        logger.info(f"Attempting to flush {len(events)} offline buffered incidents...")
        remaining = []

        for payload in events:
            if self._post_with_retry(payload):
                logger.info(f"Flushed buffered incident [{payload.get('incident_id')}]")
            else:
                remaining.append(payload)
                break  # Stop flushing if backend is still offline

        try:
            with open(self.offline_buffer_file, "w", encoding="utf-8") as f:
                json.dump(remaining, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update offline buffer file after flush: {e}")

# AI Accident Detection & Emergency Alert Module Specification

## 1. Overview
The AI Accident Detection Module is a self-contained, modular computer vision processing engine designed for highway collision monitoring, severity classification, clean evidence capture, and automated reporting to the FastAPI Backend.

---

## 2. Architecture & Directory Structure
```
ai_module/
├── config.py                 # Central configuration and hyperparameters
├── pipeline.py               # Main unified orchestrator (AccidentDetectionPipeline)
├── camera/                   # Camera Input Support
│   ├── base.py               # Abstract BaseCameraStream and FrameData
│   ├── system_camera.py      # OpenCV webcam capture with auto-reconnect
│   ├── mobile_camera.py      # Mobile browser stream receiver & transport API
│   ├── external_camera.py    # External RTSP/IP camera reader (masked credentials)
│   └── manager.py            # Unified CameraInputManager
├── detection/                # Vehicle Detection Pipeline
│   └── yolo_detector.py      # Ultralytics YOLO11 model wrapper
├── tracking/                 # Multi-Object Vehicle Tracking
│   └── tracker.py            # IoU + Centroid Multi-Object Tracker
├── collision/                # Collision Physics & Temporal Event Detector
│   └── analyzer.py           # Multi-frame velocity drops, overlap, and temporal confirmation
├── severity/                 # Severity Classification Engine
│   └── classifier.py         # 3-tier severity classifier (High, Medium, Low) & review flag
├── capture/                  # Evidence Capture & Visualization
│   └── capture_service.py    # Pristine clean evidence saver + annotated preview drawer
├── location/                 # Spatial Location & GPS Resolver
│   └── location_service.py   # Fixed camera GPS registry & mobile GPS override
├── integration/              # FastAPI Backend Integration
│   └── backend_client.py     # HTTP client with retry, idempotency & offline buffer
└── evaluation/               # Benchmarking & Performance Monitoring
    └── evaluator.py          # Latency timer, hardware resource monitor & metric evaluator
```

---

## 3. Core Component Interfaces

### 3.1 Unified Camera Input Interface (`BaseCameraStream`)
All camera hardware streams conform to `BaseCameraStream`:
- `start() -> bool`
- `pause() -> None`
- `resume() -> None`
- `stop() -> None`
- `read_frame() -> Optional[FrameData]`
- `is_connected() -> bool`
- `get_health() -> StreamHealth`

#### Mobile Video Transport API
Mobile browsers submit frames via `MobileCameraStream.push_frame()`:
```python
push_frame(
    frame_input: Union[bytes, str, np.ndarray],  # raw bytes, base64 data string, or BGR ndarray
    timestamp: Optional[datetime] = None,
    gps_coords: Optional[Dict[str, float]] = None  # {"latitude": float, "longitude": float}
) -> bool
```

---

### 3.2 Vehicle Detection (`YOLO11Detector`)
- **Supported Vehicle Classes:** Cars (`2`), Motorcycles (`3`), Buses (`5`), Trucks (`7`).
- **Configurable Parameters:**
  - `conf_threshold`: Default `0.35`
  - `iou_threshold`: Default `0.45`
  - `inference_size`: Default `640` (or `320` for low-spec edge hardware)
  - `model_path`: Path to YOLO11 weights (e.g., `yolo11n.pt`, `yolo11s.pt`)

---

### 3.3 Collision Analysis (`CollisionAnalyzer`)
Calculates physics metrics over sliding multi-frame window:
- **Velocity Drop:** Relative drop in speed \((v_{past} - v_{current}) / v_{past}\) > threshold.
- **Bounding Box Overlap:** Bounding box Intersection over Min Area (\(IoU_{min}\)) > threshold.
- **Unusual Proximity:** Centroid distance \(\le \text{threshold\_px}\).
- **Post-Impact Standstill:** Vehicle immobilization frames \(\ge 3\).

#### Event Lifecycle States:
1. `POTENTIAL_CANDIDATE`: Threshold crossed on frame 1.
2. `CONFIRMED`: Candidate metrics persist across \(N\) consecutive frames (`CONFIRMATION_FRAMES = 3`).
3. `COOLDOWN`: Suppresses duplicate event alerts for `COOLDOWN_SECONDS` (default 8.0s).

---

### 3.4 Severity Estimation (`SeverityClassifier`)
Three severity categories with review-required flags:
- **`HIGH`**: Severe overlap (\(IoU > 0.40\)), severe deceleration (\(> 70\%\)), or multi-vehicle crash (\(\ge 3\)).
- **`MEDIUM`**: Moderate collision metrics without meeting High threshold.
- **`LOW`**: Low-impact event or minor disruption.
- **`review_required` Flag:** Set to `True` if confidence \(< 0.60\) or visual evidence is ambiguous.

---

### 3.5 Evidence Preservation (`EvidenceCaptureService`)
For every confirmed accident:
1. **Clean Image:** Pristine original video frame stored without overlays (e.g. `ACC-20261007-0001_clean.jpg`).
2. **Annotated Image:** Visual dashboard preview rendered with vehicle bounding boxes, track IDs, confidence scores, and severity badge overlay (e.g. `ACC-20261007-0001_annotated.jpg`).

---

### 3.6 Backend Integration Client (`BackendIntegrationClient`)
Submits `POST /api/v1/incidents` matching the FastAPI Pydantic schema `IncidentCreate`:
```json
{
  "incident_id": "ACC-20261007231500-0001",
  "camera_external_id": "CAM-SYS-01",
  "detected_at": "2026-10-07T23:15:00+00:00",
  "accident_detected": true,
  "severity": "high",
  "confidence_score": 0.88,
  "latitude": 37.7749,
  "longitude": -122.4194,
  "location_description": "Highway 101 North - KM 42",
  "accident_image_url": "/static/evidence/ACC-20261007231500-0001_clean.jpg",
  "vehicle_count": 2,
  "vehicle_info": {
    "vehicle_count": 2,
    "breakdown": {"car": 1, "truck": 1}
  },
  "ai_event_data": {
    "review_required": false,
    "severity_reasons": ["Significant vehicle bounding box overlap", "Severe abrupt deceleration"],
    "annotated_image_url": "/static/evidence/ACC-20261007231500-0001_annotated.jpg"
  },
  "idempotency_key": "IDEM-CAM-SYS-01-ACC-20261007231500-0001"
}
```

---

## 4. Safety & Compliance Disclaimer
> **IMPORTANT:** AI severity classification is strictly based on visual motion dynamics and bounding box trajectories. The system **does NOT estimate actual human injuries, fatalities, or medical condition** from camera footage.

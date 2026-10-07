"""
AI Module Configuration
Defines setup, thresholds, model paths, camera settings, and backend integration parameters.
"""

import os
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel, Field

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

class AIConfig(BaseModel):
    # Model Configurations
    YOLO_MODEL_PATH: str = Field(
        default=os.getenv("YOLO_MODEL_PATH", "yolo11n.pt"),
        description="Path or model identifier for YOLO11 weights"
    )
    CONFIDENCE_THRESHOLD: float = Field(
        default=float(os.getenv("YOLO_CONFIDENCE", "0.35")),
        description="Minimum detection confidence threshold"
    )
    IOU_THRESHOLD: float = Field(
        default=float(os.getenv("YOLO_IOU", "0.45")),
        description="NMS IoU threshold"
    )
    INFERENCE_SIZE: int = Field(
        default=int(os.getenv("INFERENCE_SIZE", "640")),
        description="Image resolution for inference (e.g. 640, 320)"
    )
    FRAME_STRIDE: int = Field(
        default=int(os.getenv("FRAME_STRIDE", "1")),
        description="Process every Nth frame to save compute"
    )

    # Vehicle COCO Class IDs
    # 2: car, 3: motorcycle, 5: bus, 7: truck
    VEHICLE_CLASS_IDS: List[int] = Field(default=[2, 3, 5, 7])
    VEHICLE_CLASS_NAMES: Dict[int, str] = Field(
        default={2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
    )

    # Collision & Temporal Tracking Parameters
    TRACK_HISTORY_FRAMES: int = Field(
        default=30,
        description="Number of frames to maintain movement history"
    )
    VELOCITY_DROP_THRESHOLD: float = Field(
        default=0.45,
        description="Relative speed drop threshold indicating sudden stop/impact"
    )
    OVERLAP_THRESHOLD: float = Field(
        default=0.15,
        description="Intersection over Min Area ratio indicating collision overlap"
    )
    PROXIMITY_THRESHOLD_PX: float = Field(
        default=45.0,
        description="Pixel distance threshold for vehicle proximity warning"
    )
    CONFIRMATION_FRAMES: int = Field(
        default=3,
        description="Temporal frames required to confirm collision event"
    )
    COOLDOWN_SECONDS: float = Field(
        default=8.0,
        description="Cooldown period in seconds to prevent duplicate event submissions"
    )

    # Evidence Capture & Storage
    STORAGE_DIR: Path = Field(
        default=BASE_DIR / "storage" / "evidence",
        description="Directory to store clean evidence images and previews"
    )
    PRE_EVENT_BUFFER_FRAMES: int = Field(
        default=30,
        description="Pre-event ring buffer frame count"
    )
    POST_EVENT_BUFFER_FRAMES: int = Field(
        default=30,
        description="Post-event ring buffer frame count"
    )

    # Backend Integration
    BACKEND_API_URL: str = Field(
        default=os.getenv("BACKEND_API_URL", "http://localhost:8000"),
        description="FastAPI Backend root URL"
    )
    INCIDENT_ENDPOINT: str = Field(
        default="/api/v1/incidents",
        description="Backend API endpoint for incident submission"
    )
    REQUEST_TIMEOUT: float = Field(default=5.0)
    MAX_RETRIES: int = Field(default=3)
    OFFLINE_BUFFER_FILE: Path = Field(
        default=BASE_DIR / "storage" / "offline_incidents.json"
    )

    # Device Setup
    DEVICE: str = Field(
        default=os.getenv("AI_DEVICE", "cpu"),
        description="Inference device: cpu, cuda, or mps"
    )

    class Config:
        arbitrary_types_allowed = True

settings = AIConfig()

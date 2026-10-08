"""
Vehicle Detection Module using Ultralytics YOLO11
Detects Cars, Motorcycles, Buses, Trucks, and road vehicles.
Supports configurable model size, resolution, confidence filtering, and frame sampling.
"""

from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from ai_module.config import settings

logger = logging.getLogger(__name__)

# Try importing ultralytics, set flag if missing or if torch fails
try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except Exception as e:
    logger.warning(f"Ultralytics YOLO import warning: {e}. Detector fallback will be available.")
    ULTRALYTICS_AVAILABLE = False


@dataclass
class DetectedVehicle:
    box: Tuple[float, float, float, float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str
    track_id: Optional[int] = None
    center: Tuple[float, float] = (0.0, 0.0)
    area: float = 0.0

    def __post_init__(self):
        x1, y1, x2, y2 = self.box
        self.center = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
        self.area = max(0.0, (x2 - x1)) * max(0.0, (y2 - y1))


@dataclass
class DetectionResult:
    frame_id: int
    timestamp: datetime
    camera_id: str
    vehicles: List[DetectedVehicle]
    vehicle_count: int
    count_by_class: Dict[str, int]
    inference_time_ms: float
    resolution: Tuple[int, int]


class YOLO11Detector:
    """
    YOLO11 Vehicle Detector wrapper with filtering and hardware optimization options.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        inference_size: Optional[int] = None,
        vehicle_class_ids: Optional[List[int]] = None,
        device: Optional[str] = None
    ):
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self.conf_threshold = conf_threshold or settings.CONFIDENCE_THRESHOLD
        self.iou_threshold = iou_threshold or settings.IOU_THRESHOLD
        self.imgsz = inference_size or settings.INFERENCE_SIZE
        self.vehicle_class_ids = vehicle_class_ids or settings.VEHICLE_CLASS_IDS
        self.device = device or settings.DEVICE

        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Load YOLO11 model weights safely."""
        if not ULTRALYTICS_AVAILABLE:
            logger.warning("Ultralytics unavailable; YOLO11 detector operating in fallback mode.")
            return

        try:
            logger.info(f"Loading YOLO11 model: {self.model_path} on device {self.device}")
            self.model = YOLO(self.model_path)
            # Warm up model if possible
            dummy = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
            self.model(dummy, verbose=False, device=self.device, imgsz=self.imgsz)
            logger.info("YOLO11 model initialized and warmed up successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLO11 model weights from '{self.model_path}': {e}")
            logger.warning("YOLO11 detector falling back to heuristic/synthetic detection mode.")
            self.model = None

    def update_config(
        self,
        conf_threshold: Optional[float] = None,
        inference_size: Optional[int] = None,
        model_path: Optional[str] = None
    ):
        """Dynamically update detection configuration for target hardware."""
        if conf_threshold is not None:
            self.conf_threshold = conf_threshold
        if inference_size is not None:
            self.imgsz = inference_size
        if model_path is not None and model_path != self.model_path:
            self.model_path = model_path
            self._initialize_model()

    def detect(
        self,
        image: np.ndarray,
        frame_id: int,
        timestamp: datetime,
        camera_id: str
    ) -> DetectionResult:
        """
        Perform vehicle detection on an input BGR frame.
        """
        import time
        t0 = time.time()
        h, w = image.shape[:2]

        vehicles: List[DetectedVehicle] = []
        count_by_class: Dict[str, int] = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "other": 0}

        if self.model is not None:
            try:
                results = self.model(
                    image,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    imgsz=self.imgsz,
                    device=self.device,
                    classes=self.vehicle_class_ids,
                    verbose=False
                )

                if results and len(results) > 0:
                    boxes = results[0].boxes
                    if boxes is not None and len(boxes) > 0:
                        for box in boxes:
                            xyxy = box.xyxy[0].cpu().numpy().tolist()
                            conf = float(box.conf[0].cpu().numpy())
                            cls_id = int(box.cls[0].cpu().numpy())
                            cls_name = settings.VEHICLE_CLASS_NAMES.get(cls_id, "vehicle")

                            vehicle = DetectedVehicle(
                                box=(float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])),
                                confidence=conf,
                                class_id=cls_id,
                                class_name=cls_name
                            )
                            vehicles.append(vehicle)

                            c_key = cls_name if cls_name in count_by_class else "other"
                            count_by_class[c_key] += 1
            except Exception as e:
                logger.error(f"YOLO11 inference error on frame {frame_id}: {e}")

        # Fallback / contour heuristic detection if YOLO model is unavailable
        if self.model is None and len(vehicles) == 0:
            vehicles, count_by_class = self._heuristic_fallback_detect(image)

        dt_ms = (time.time() - t0) * 1000.0

        return DetectionResult(
            frame_id=frame_id,
            timestamp=timestamp,
            camera_id=camera_id,
            vehicles=vehicles,
            vehicle_count=len(vehicles),
            count_by_class=count_by_class,
            inference_time_ms=dt_ms,
            resolution=(w, h)
        )

    def _heuristic_fallback_detect(
        self,
        image: np.ndarray
    ) -> Tuple[List[DetectedVehicle], Dict[str, int]]:
        """
        Fallback vehicle motion/blob detector when YOLO weights are missing or CPU-constrained.
        """
        vehicles = []
        counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "other": 0}

        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            h, w = image.shape[:2]
            min_area = (w * h) * 0.005  # 0.5% frame area min for vehicle blob

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > min_area:
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    # Exclude edge artifacts or whole frame contours
                    if bw >= w * 0.95 or bh >= h * 0.95:
                        continue

                    aspect_ratio = bw / float(bh)
                    cls_name = "car"
                    cls_id = 2
                    if area > (w * h) * 0.08:
                        cls_name = "truck" if aspect_ratio > 1.2 else "bus"
                        cls_id = 7 if cls_name == "truck" else 5

                    veh = DetectedVehicle(
                        box=(float(x), float(y), float(x + bw), float(y + bh)),
                        confidence=0.60,
                        class_id=cls_id,
                        class_name=cls_name
                    )
                    vehicles.append(veh)
                    counts[cls_name] += 1
        except Exception as e:
            logger.debug(f"Heuristic vehicle detection error: {e}")

        return vehicles, counts

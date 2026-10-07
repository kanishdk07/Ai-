"""
Vehicle Detection Package
"""

from .yolo_detector import YOLO11Detector, DetectedVehicle, DetectionResult

__all__ = ["YOLO11Detector", "DetectedVehicle", "DetectionResult"]

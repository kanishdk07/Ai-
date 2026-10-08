"""
AI Highway Accident Detection Module Package
"""

from .config import settings, AIConfig
from .pipeline import AccidentDetectionPipeline

__all__ = ["settings", "AIConfig", "AccidentDetectionPipeline"]

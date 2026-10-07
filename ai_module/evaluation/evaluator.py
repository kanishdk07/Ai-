"""
AI Performance Monitoring & Model Evaluator
Monitors CPU/GPU/memory usage, latency, and computes evaluation metrics (Precision, Recall, F1, False Alarm Rate).
"""

from dataclasses import dataclass, field
import logging
import time
from typing import List, Dict, Any, Optional
import numpy as np
import psutil

logger = logging.getLogger(__name__)

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except Exception:
    CUDA_AVAILABLE = False


@dataclass
class HardwareMetrics:
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    gpu_memory_mb: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None


@dataclass
class PerformanceReport:
    total_frames_processed: int
    avg_inference_latency_ms: float
    avg_total_latency_ms: float
    throughput_fps: float
    hardware: HardwareMetrics


@dataclass
class EvaluationMetrics:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    false_alarm_rate_per_hour: float
    severity_accuracy: float
    confusion_matrix: Dict[str, Dict[str, int]]


class PerformanceMonitor:
    """
    Real-time system resource and latency tracker for the AI pipeline.
    """

    def __init__(self):
        self.inference_times: List[float] = []
        self.total_pipeline_times: List[float] = []
        self.start_time = time.time()
        self.total_frames = 0

    def record_frame(self, inference_ms: float, total_ms: float):
        self.inference_times.append(inference_ms)
        self.total_pipeline_times.append(total_ms)
        self.total_frames += 1
        if len(self.inference_times) > 1000:
            self.inference_times.pop(0)
            self.total_pipeline_times.pop(0)

    def get_hardware_metrics(self) -> HardwareMetrics:
        cpu_p = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        mem_mb = mem.used / (1024 * 1024)
        mem_p = mem.percent

        gpu_mem = None
        gpu_util = None

        if CUDA_AVAILABLE:
            try:
                gpu_mem = torch.cuda.memory_allocated() / (1024 * 1024)
            except Exception:
                pass

        return HardwareMetrics(
            cpu_percent=cpu_p,
            memory_mb=mem_mb,
            memory_percent=mem_p,
            gpu_memory_mb=gpu_mem,
            gpu_utilization_percent=gpu_util
        )

    def generate_report(self) -> PerformanceReport:
        dt = max(0.001, time.time() - self.start_time)
        fps = self.total_frames / dt
        avg_inf = float(np.mean(self.inference_times)) if self.inference_times else 0.0
        avg_tot = float(np.mean(self.total_pipeline_times)) if self.total_pipeline_times else 0.0

        return PerformanceReport(
            total_frames_processed=self.total_frames,
            avg_inference_latency_ms=round(avg_inf, 2),
            avg_total_latency_ms=round(avg_tot, 2),
            throughput_fps=round(fps, 2),
            hardware=self.get_hardware_metrics()
        )


class PipelineEvaluator:
    """
    Evaluation tool for calculating accuracy, precision, recall, and false alarm rate.
    """

    @staticmethod
    def evaluate_ground_truth(
        predictions: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]],
        test_duration_hours: float = 1.0
    ) -> EvaluationMetrics:
        """
        Evaluate AI pipeline output against labeled test video ground truth.
        """
        tp = 0
        fp = 0
        fn = 0
        correct_severity = 0
        total_accidents = len(ground_truth)

        # Confusion matrix for severity categories: High, Medium, Low
        categories = ["high", "medium", "low"]
        conf_matrix = {c1: {c2: 0 for c2 in categories} for c1 in categories}

        # Match predictions to ground truth items by time window or frame range
        matched_gt = set()

        for pred in predictions:
            pred_time = pred.get("timestamp")
            pred_sev = pred.get("severity", "low").lower()

            match_found = False
            for gt_idx, gt in enumerate(ground_truth):
                gt_time = gt.get("timestamp")
                gt_sev = gt.get("severity", "low").lower()

                # Check if timestamp match is within 5 seconds window
                if abs((pred_time - gt_time).total_seconds()) <= 5.0 and gt_idx not in matched_gt:
                    tp += 1
                    matched_gt.add(gt_idx)
                    match_found = True

                    if pred_sev == gt_sev:
                        correct_severity += 1

                    if pred_sev in categories and gt_sev in categories:
                        conf_matrix[gt_sev][pred_sev] += 1
                    break

            if not match_found:
                fp += 1

        fn = total_accidents - len(matched_gt)

        precision = tp / max(1, (tp + fp))
        recall = tp / max(1, (tp + fn))
        f1 = (2 * precision * recall) / max(0.0001, (precision + recall))
        false_alarm_rate = fp / max(0.1, test_duration_hours)
        severity_acc = correct_severity / max(1, tp)

        return EvaluationMetrics(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            false_alarm_rate_per_hour=round(false_alarm_rate, 2),
            severity_accuracy=round(severity_acc, 4),
            confusion_matrix=conf_matrix
        )

"""
AI Pipeline Evaluation Script
Runs model benchmark evaluation over test video streams or simulated incidents.
Outputs metric scores (Precision, Recall, F1, False Alarm Rate) and documented hardware performance.
"""

import argparse
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from ai_module.config import settings
from ai_module.camera.manager import CameraInputManager
from ai_module.pipeline import AccidentDetectionPipeline
from ai_module.evaluation.evaluator import PipelineEvaluator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("evaluate_pipeline")


def generate_synthetic_ground_truth(duration_sec: int = 10) -> list:
    """Generate sample ground truth for benchmarking when test labels file is omitted."""
    now = datetime.now(timezone.utc)
    return [
        {
            "timestamp": now + timedelta(seconds=3),
            "severity": "high",
            "description": "Simulated rear-end highway collision"
        }
    ]


def run_evaluation(video_path: Path, ground_truth_path: Path = None, max_frames: int = 300):
    logger.info(f"Starting pipeline evaluation on: {video_path}")

    cam_mgr = CameraInputManager()
    cam_id = "CAM-EVAL-01"
    cam_mgr.register_file_camera(cam_id, file_path=str(video_path), loop=False)

    pipeline = AccidentDetectionPipeline(
        camera_manager=cam_mgr,
        enable_backend_submission=False
    )

    if not cam_mgr.start_stream(cam_id):
        logger.error(f"Could not open evaluation video file: {video_path}")
        return

    predictions = []
    frame_count = 0

    while frame_count < max_frames:
        frame_data = cam_mgr.read_frame(cam_id)
        if frame_data is None:
            break

        confirmed, candidates, _ = pipeline.process_frame(frame_data)
        frame_count += 1

        if confirmed:
            predictions.append({
                "timestamp": confirmed.created_at,
                "severity": confirmed.evidence.raw_metrics.get("severity", "medium"),
                "event_id": confirmed.event_id,
                "confidence": confirmed.confidence_score
            })

    cam_mgr.stop_all()

    # Load Ground Truth
    ground_truth = []
    if ground_truth_path and ground_truth_path.exists():
        try:
            with open(ground_truth_path, "r", encoding="utf-8") as f:
                gt_raw = json.load(f)
                for item in gt_raw:
                    item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                    ground_truth.append(item)
        except Exception as e:
            logger.warning(f"Could not load ground truth JSON ({e}); using synthetic test benchmark.")
            ground_truth = generate_synthetic_ground_truth()
    else:
        ground_truth = generate_synthetic_ground_truth()

    metrics = PipelineEvaluator.evaluate_ground_truth(
        predictions=predictions,
        ground_truth=ground_truth,
        test_duration_hours=(frame_count / 30.0) / 3600.0
    )

    report = pipeline.get_performance_report()

    print("\n" + "=" * 60)
    print("       AI HIGHWAY ACCIDENT DETECTION EVALUATION REPORT       ")
    print("=" * 60)
    print(f"Evaluation Video Target: {video_path}")
    print(f"Total Frames Processed: {metrics.true_positives + metrics.false_positives + metrics.false_negatives} detections evaluated")
    print("-" * 60)
    print(f"True Positives (TP):   {metrics.true_positives}")
    print(f"False Positives (FP):  {metrics.false_positives}")
    print(f"False Negatives (FN):  {metrics.false_negatives}")
    print(f"Precision:             {metrics.precision * 100:.2f}%")
    print(f"Recall:                {metrics.recall * 100:.2f}%")
    print(f"F1-Score:              {metrics.f1_score * 100:.2f}%")
    print(f"False Alarm Rate:      {metrics.false_alarm_rate_per_hour:.2f} per hour")
    print(f"Severity Accuracy:     {metrics.severity_accuracy * 100:.2f}%")
    print("-" * 60)
    print("HARDWARE & LATENCY BENCHMARK:")
    print(f"Inference Latency:     {report.avg_inference_latency_ms} ms")
    print(f"Total Frame Latency:   {report.avg_total_latency_ms} ms")
    print(f"Processing Throughput: {report.throughput_fps} FPS")
    print(f"CPU Percent:           {report.hardware.cpu_percent}%")
    print(f"RAM Used:              {report.hardware.memory_mb:.1f} MB ({report.hardware.memory_percent}%)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AI Pipeline on Labeled Video Benchmark")
    parser.add_argument("--video", type=str, default="test_video.mp4", help="Test video file path")
    parser.add_argument("--gt", type=str, default=None, help="Ground truth JSON metadata path")
    parser.add_argument("--max-frames", type=int, default=300, help="Maximum frames to evaluate")
    args = parser.parse_args()

    run_evaluation(Path(args.video), Path(args.gt) if args.gt else None, args.max_frames)

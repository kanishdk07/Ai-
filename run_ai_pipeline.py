"""
AI Pipeline Standalone Command Line Application
Run the AI Highway Accident Detection pipeline on a webcam, manual video upload file, RTSP IP stream, or mobile input.
"""

import argparse
import json
import logging
import sys
import time
import cv2

from ai_module.config import settings
from ai_module.camera.manager import CameraInputManager
from ai_module.pipeline import AccidentDetectionPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_ai_pipeline")


def parse_args():
    parser = argparse.ArgumentParser(description="AI Highway Accident Detection System Pipeline")
    parser.add_argument("--source", type=str, choices=["webcam", "file", "rtsp", "mobile", "upload"], default="webcam",
                        help="Input video source type (webcam, file, rtsp, mobile, upload)")
    parser.add_argument("--camera-id", type=str, default="CAM-SYSTEM-01",
                        help="Camera Identifier string")
    parser.add_argument("--path", type=str, default=None,
                        help="Video file path or RTSP stream URL")
    parser.add_argument("--device-index", type=int, default=0,
                        help="Webcam device index (0, 1, 2...)")
    parser.add_argument("--conf", type=float, default=settings.CONFIDENCE_THRESHOLD,
                        help="YOLO detection confidence threshold")
    parser.add_argument("--lat", type=float, default=None,
                        help="Latitude coordinate for trusted location metadata")
    parser.add_argument("--lng", type=float, default=None,
                        help="Longitude coordinate for trusted location metadata")
    parser.add_argument("--loc-desc", type=str, default=None,
                        help="Location description text")
    parser.add_argument("--backend-url", type=str, default=settings.BACKEND_API_URL,
                        help="FastAPI backend URL")
    parser.add_argument("--no-backend", action="store_true",
                        help="Disable submission to FastAPI backend")
    parser.add_argument("--display", action="store_true",
                        help="Show live GUI window preview with bounding boxes")
    parser.add_argument("--max-frames", type=int, default=None,
                        help="Limit processing to N frames")
    parser.add_argument("--json-output", action="store_true",
                        help="Output structured JSON result to stdout for upload processing")
    return parser.parse_args()


def main():
    args = parse_args()

    # Manual Video Upload mode processing
    if args.source in ["upload", "file"] and args.json_output:
        if not args.path:
            logger.error("--path argument required when using --json-output / manual upload")
            sys.exit(1)

        pipeline = AccidentDetectionPipeline(enable_backend_submission=not args.no_backend)
        pipeline.detector.conf_threshold = args.conf

        loc_meta = None
        if args.lat is not None and args.lng is not None:
            loc_meta = {
                "latitude": args.lat,
                "longitude": args.lng,
                "location_description": args.loc_desc or f"GPS ({args.lat:.4f}, {args.lng:.4f})",
                "source": "provided_gps",
                "location_status": "verified"
            }

        res = pipeline.process_video_file(
            video_path=args.path,
            camera_id=args.camera_id,
            location_metadata=loc_meta,
            submit_to_backend=not args.no_backend
        )
        print(json.dumps(res, indent=2))
        return

    logger.info("Initializing AI Highway Accident Detection Pipeline...")
    cam_mgr = CameraInputManager()

    cam_id = args.camera_id
    if args.source == "webcam":
        cam_mgr.register_system_camera(cam_id, device_index=args.device_index)
    elif args.source in ["file", "upload"]:
        if not args.path:
            logger.error("--path argument required when using --source file/upload")
            sys.exit(1)
        cam_mgr.register_file_camera(cam_id, file_path=args.path)
    elif args.source == "rtsp":
        if not args.path:
            logger.error("--path argument required when using --source rtsp")
            sys.exit(1)
        cam_mgr.register_external_camera(cam_id, stream_url=args.path)
    elif args.source == "mobile":
        cam_mgr.register_mobile_camera(cam_id)

    pipeline = AccidentDetectionPipeline(
        camera_manager=cam_mgr,
        enable_backend_submission=not args.no_backend
    )
    pipeline.detector.conf_threshold = args.conf

    if args.lat is not None and args.lng is not None:
        pipeline.location_registry.register_camera_location(
            camera_id=cam_id,
            latitude=args.lat,
            longitude=args.lng,
            location_description=args.loc_desc or f"Camera [{cam_id}]"
        )

    if not cam_mgr.start_stream(cam_id):
        logger.error(f"Failed to start camera stream [{cam_id}]. Exiting.")
        sys.exit(1)

    logger.info(f"Pipeline active. Processing stream [{cam_id}]...")

    frames_processed = 0
    try:
        while True:
            frame_data = cam_mgr.read_frame(cam_id)
            if frame_data is None:
                time.sleep(0.01)
                if args.source in ["file", "upload"] and cam_mgr.get_stream(cam_id).status == "offline":
                    break
                continue

            confirmed_evt, candidate_evts, preview_img = pipeline.process_frame(frame_data)
            frames_processed += 1

            if confirmed_evt:
                logger.info(f"🚨 [ACCIDENT CONFIRMED] Event {confirmed_evt.event_id} (Conf: {confirmed_evt.confidence_score})")

            if args.display:
                cv2.imshow("AI Highway Accident Detection", preview_img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            if args.max_frames and frames_processed >= args.max_frames:
                break

    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user interrupt.")
    finally:
        cam_mgr.stop_all()
        if args.display:
            cv2.destroyAllWindows()

        report = pipeline.get_performance_report()
        logger.info("--- PIPELINE PERFORMANCE REPORT ---")
        logger.info(f"Total Frames Processed: {report.total_frames_processed}")
        logger.info(f"Throughput FPS: {report.throughput_fps} FPS")
        logger.info(f"Avg Inference Latency: {report.avg_inference_latency_ms} ms")
        logger.info(f"Avg Total Latency: {report.avg_total_latency_ms} ms")
        logger.info(f"CPU Percent: {report.hardware.cpu_percent}%")
        logger.info(f"RAM Usage: {report.hardware.memory_mb:.1f} MB ({report.hardware.memory_percent}%)")


if __name__ == "__main__":
    main()

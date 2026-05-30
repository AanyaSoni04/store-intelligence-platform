"""
CLI entry point for running the detection pipeline on a video file.

Usage:
    python -m scripts.run_pipeline --video path/to/video.mp4 --store store_001 --camera cam_001

TODO: Implement:
    - Parse CLI arguments
    - Initialize DetectionPipeline
    - Run pipeline
    - Report results (events generated, processing time)
"""

import argparse
import logging

logger = logging.getLogger("store_intel")


def main():
    parser = argparse.ArgumentParser(description="Run detection pipeline on a video file")
    parser.add_argument("--video", required=True, help="Path to video file or RTSP URL")
    parser.add_argument("--store", default="store_001", help="Store ID")
    parser.add_argument("--camera", default="cam_001", help="Camera ID")
    parser.add_argument("--zone-config", default=None, help="Path to zone config JSON")
    parser.add_argument("--fps", type=int, default=5, help="Target processing FPS")
    args = parser.parse_args()

    print(f"Processing: {args.video}")
    print(f"Store: {args.store}, Camera: {args.camera}")

    # TODO: Initialize and run DetectionPipeline
    # from store_intel.detection.pipeline import DetectionPipeline
    # pipeline = DetectionPipeline(
    #     video_source=args.video,
    #     store_id=args.store,
    #     camera_id=args.camera,
    #     zone_config=args.zone_config,
    #     target_fps=args.fps,
    # )
    # event_count = pipeline.run()
    # print(f"Pipeline complete: {event_count} events generated")

    print("TODO: Pipeline not yet implemented")


if __name__ == "__main__":
    main()

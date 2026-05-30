import argparse
import sys
from pathlib import Path

# Ensure src is in pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from store_intel.detection.pipeline import DetectionPipeline

def main():
    parser = argparse.ArgumentParser(description="Run detection pipeline on a video file")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--camera", required=True, help="Camera ID (e.g. CAM3, CAM5)")
    parser.add_argument("--store", default="test_store", help="Store ID")
    parser.add_argument("--zone-config", default=None, help="Path to zone config JSON")
    
    args = parser.parse_args()
    
    print(f"Starting pipeline for {args.camera} on {args.video}...")
    pipeline = DetectionPipeline(
        video_source=args.video,
        store_id=args.store,
        camera_id=args.camera,
        zone_config=args.zone_config,
        target_fps=5  # Default processing fps
    )
    
    event_count = pipeline.run()
    print(f"Done! Generated {event_count} events.")
    print("Check data/generated_events.json for the output.")

if __name__ == "__main__":
    main()

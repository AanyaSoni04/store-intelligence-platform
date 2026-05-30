import argparse
import sys
from pathlib import Path
import cv2

def video_info(video_path: str):
    path = Path(video_path)
    if not path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        sys.exit(1)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    cap.release()

    duration = total_frames / fps if fps > 0 else 0

    print(f"--- Video Info: {path.name} ---")
    print(f"Resolution : {width}x{height}")
    print(f"FPS        : {fps:.2f}")
    print(f"Frame Count: {total_frames}")
    print(f"Duration   : {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print("-" * 30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get video info (resolution, fps, duration, frames).")
    parser.add_argument("video_path", type=str, help="Path to the video file")
    args = parser.parse_args()
    
    video_info(args.video_path)

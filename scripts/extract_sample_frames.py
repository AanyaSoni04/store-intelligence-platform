import argparse
import sys
from pathlib import Path
import cv2

def extract_frames(video_path: str):
    path = Path(video_path)
    if not path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    video_name = path.stem
    output_dir = Path("data/sample_frames") / video_name
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if total_frames <= 0:
        print("Error: Could not determine frame count.")
        sys.exit(1)

    print(f"Processing {video_name}...")
    print(f"Total Frames: {total_frames} | FPS: {fps:.2f}")

    percentages = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    for p in percentages:
        frame_idx = int(total_frames * p)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if ret:
            pct_str = f"{int(p * 100)}pct"
            out_file = output_dir / f"{video_name}_{pct_str}.jpg"
            cv2.imwrite(str(out_file), frame)
            print(f"Saved: {out_file} (Frame {frame_idx})")
        else:
            print(f"Failed to read frame at {int(p * 100)}%")

    cap.release()
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract sample frames from a video.")
    parser.add_argument("video_path", type=str, help="Path to the video file")
    args = parser.parse_args()
    
    extract_frames(args.video_path)

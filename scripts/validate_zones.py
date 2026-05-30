"""
Zone polygon validation script.

Runs YOLOv8n on sample frames from each camera, extracts person centroids,
and overlays them on candidate zone polygons. Produces annotated screenshots
for human review.
"""

import sys
import cv2
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultralytics import YOLO


# All cameras are 1920x1080.
# Candidate zone polygons — to be validated by this script.

CANDIDATE_ZONES = {
    "CAM1": {
        "browsing_a": {
            "color": (0, 255, 0),   # green
            "polygon": [[100, 350], [1800, 350], [1800, 1080], [100, 1080]],
            "rationale": "Floor area where customers browse shelves. Excludes top ~350px (shelf signage/ceiling). Excludes far-left/right edges (camera barrel distortion)."
        }
    },
    "CAM2": {
        "browsing_b": {
            "color": (0, 255, 0),
            "polygon": [[100, 350], [1800, 350], [1800, 1080], [100, 1080]],
            "rationale": "Browsing floor area B. Same geometry as CAM1 (similar camera angle and store layout)."
        }
    },
    "CAM3": {
        "entrance_zone": {
            "color": (0, 255, 0),
            "polygon": [[0, 150], [1920, 150], [1920, 1080], [0, 1080]],
            "rationale": "The entire walkable area in the entrance view. Leaving this zone (track lost) triggers an EXIT event."
        }
    },
    "CAM4": {
        "stockroom": {
            "color": (0, 0, 255),   # red = staff zone
            "polygon": [[100, 150], [1800, 150], [1800, 1080], [100, 1080]],
            "rationale": "Entire stockroom floor. Anyone detected here is likely staff. Excludes top ~150px (shelf/ceiling)."
        }
    },
    "CAM5": {
        "billing_queue": {
            "color": (255, 165, 0),  # orange
            "polygon": [[0, 200], [650, 200], [650, 1080], [0, 1080]],
            "rationale": "Left side of frame — floor area in front of checkout counter where customers queue."
        },
        "checkout_counter": {
            "color": (0, 0, 255),    # red
            "polygon": [[700, 200], [1920, 200], [1920, 1080], [700, 1080]],
            "rationale": "Right side of the frame, behind the counter where the staff operates."
        }
    }
}


def run_validation():
    model = YOLO("yolov8n.pt")
    
    sample_dir = Path("data/sample_frames")
    output_dir = Path("data/zone_validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cam_folders = {
        "CAM1": "CAM 1",
        "CAM2": "CAM 2",
        "CAM3": "CAM 3",
        "CAM4": "CAM 4",
        "CAM5": "CAM 5",
    }
    
    for cam_id, folder_name in cam_folders.items():
        print(f"\n{'='*60}")
        print(f"Processing {cam_id}")
        print(f"{'='*60}")
        
        cam_dir = sample_dir / folder_name
        if not cam_dir.exists():
            print(f"  SKIP: {cam_dir} not found")
            continue
        
        frames = sorted(cam_dir.glob("*.jpg"))
        zones = CANDIDATE_ZONES.get(cam_id, {})
        
        for frame_path in frames:
            img = cv2.imread(str(frame_path))
            if img is None:
                continue
            
            h, w = img.shape[:2]
            annotated = img.copy()
            
            # Draw candidate zone polygons
            for zone_id, zone_info in zones.items():
                pts = np.array(zone_info["polygon"], np.int32).reshape((-1, 1, 2))
                color = zone_info["color"]
                
                # Draw filled polygon with transparency
                overlay = annotated.copy()
                cv2.fillPoly(overlay, [pts], color)
                cv2.addWeighted(overlay, 0.2, annotated, 0.8, 0, annotated)
                
                # Draw polygon border
                cv2.polylines(annotated, [pts], True, color, 2)
                
                # Label
                top_left = zone_info["polygon"][0]
                cv2.putText(annotated, zone_id, (top_left[0] + 5, top_left[1] + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Run YOLO detection
            results = model.predict(img, classes=[0], conf=0.45, verbose=False)
            result = results[0]
            
            centroids_inside = {z: 0 for z in zones}
            centroids_outside = 0
            total_detections = 0
            
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    
                    # Bottom-center centroid (matches tracker.py L97-98)
                    cx = (x1 + x2) / 2.0
                    cy = float(y2)
                    
                    total_detections += 1
                    
                    # Draw bbox
                    cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 255), 1)
                    
                    # Check which zones contain centroid
                    in_any_zone = False
                    for zone_id, zone_info in zones.items():
                        pts_np = np.array(zone_info["polygon"], dtype=np.float32)
                        inside = cv2.pointPolygonTest(pts_np, (cx, cy), False) >= 0
                        if inside:
                            centroids_inside[zone_id] += 1
                            in_any_zone = True
                    
                    if not in_any_zone:
                        centroids_outside += 1
                    
                    # Draw centroid
                    color_c = (0, 255, 255) if in_any_zone else (0, 0, 255)
                    cv2.circle(annotated, (int(cx), int(cy)), 6, color_c, -1)
                    cv2.putText(annotated, f"{conf:.2f}", (int(cx) + 8, int(cy) - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_c, 1)
            
            # Summary text on image
            y_text = 30
            cv2.putText(annotated, f"{cam_id} | {frame_path.stem}", (10, y_text),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_text += 30
            cv2.putText(annotated, f"Detections: {total_detections}", (10, y_text),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            for zone_id, count in centroids_inside.items():
                y_text += 25
                cv2.putText(annotated, f"  {zone_id}: {count} inside", (10, y_text),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            y_text += 25
            cv2.putText(annotated, f"  outside all zones: {centroids_outside}", (10, y_text),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Save annotated image
            out_path = output_dir / f"{cam_id}_{frame_path.stem}.jpg"
            cv2.imwrite(str(out_path), annotated)
            
            # Console output
            print(f"  {frame_path.stem}: {total_detections} detections")
            for zone_id, count in centroids_inside.items():
                print(f"    {zone_id}: {count} inside")
            print(f"    outside: {centroids_outside}")
        
        # Print rationale
        for zone_id, zone_info in zones.items():
            print(f"\n  Zone '{zone_id}' rationale:")
            print(f"    {zone_info['rationale']}")
    
    print(f"\n{'='*60}")
    print(f"Annotated images saved to: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_validation()

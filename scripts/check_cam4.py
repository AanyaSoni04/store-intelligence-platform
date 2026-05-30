import cv2
import sys
sys.path.insert(0, 'src')
from store_intel.detection.detector import PersonDetector

cap = cv2.VideoCapture('c:/Users/sonir/Downloads/CCTV Footage/CAM 4.mp4')
detector = PersonDetector()
count = 0
found = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    count += 1
    if count % 10 == 0:
        det = detector.detect(frame)
        if det:
            print(f"Found person at frame {count}: {det}")
            found += 1
            if found > 5:
                break
print(f"Checked {count} frames. Found people in {found} sampled frames.")

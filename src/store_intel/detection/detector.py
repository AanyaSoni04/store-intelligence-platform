"""
Person detector — YOLOv8 wrapper.
"""

import logging
from dataclasses import dataclass
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

logger = logging.getLogger("store_intel")


@dataclass
class Detection:
    """A single person detection."""
    bbox: tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int = 0  # 0 = person in COCO


class PersonDetector:
    """
    YOLOv8 person detector wrapper.

    Usage:
        detector = PersonDetector(model_name="yolov8n.pt", confidence=0.45)
        detections = detector.detect(frame)
    """

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.45):
        self.model_name = model_name
        self.confidence = confidence
        
        if YOLO is not None:
            logger.info(f"Loading YOLO model: {model_name}")
            self.model = YOLO(model_name)
            # Suppress verbose output
            self.model.verbose = False
        else:
            logger.warning("YOLO is not available. Falling back to synthetic detections.")
            self.model = None

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """
        Run person detection on a single frame.
        """
        # Run inference, restricting to class 0 (person)
        # verbose=False reduces terminal spam
        results = self.model.predict(frame, classes=[0], conf=self.confidence, verbose=False)
        
        detections = []
        
        # We only passed one frame, so there's one result
        result = results[0]
        
        if result.boxes is not None:
            for box in result.boxes:
                # box.xyxy is shape (1, 4)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                
                detections.append(
                    Detection(
                        bbox=(float(x1), float(y1), float(x2), float(y2)),
                        confidence=conf,
                        class_id=cls_id
                    )
                )
                
        return detections

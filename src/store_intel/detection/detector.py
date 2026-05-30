"""
Person detector — YOLOv8 wrapper.

TODO: Implement PersonDetector class with:
    - __init__(model_name, confidence_threshold): load YOLOv8 model
    - detect(frame): run inference, filter to class=person, return detections
    - Detection dataclass: bbox, confidence, class_id
"""

import logging
from dataclasses import dataclass

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

    TODO: Implement using ultralytics.YOLO.

    Usage:
        detector = PersonDetector(model_name="yolov8n.pt", confidence=0.45)
        detections = detector.detect(frame)
    """

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.45):
        self.model_name = model_name
        self.confidence = confidence
        # TODO: Load YOLO model: self.model = YOLO(model_name)

    def detect(self, frame) -> list[Detection]:
        """
        Run person detection on a single frame.

        TODO: Implement:
            - Run model inference
            - Filter to class_id == 0 (person)
            - Apply confidence threshold
            - Return list of Detection objects
        """
        raise NotImplementedError("PersonDetector not yet implemented")

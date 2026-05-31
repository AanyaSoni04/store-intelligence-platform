"""
Unit tests for PersonDetector.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from store_intel.detection.detector import PersonDetector, Detection

class TestPersonDetector:
    @patch('store_intel.detection.detector.YOLO')
    def test_detector_initialization(self, mock_yolo):
        detector = PersonDetector(model_name="yolov8n.pt", confidence=0.5)
        mock_yolo.assert_called_once_with("yolov8n.pt")
        assert detector.confidence == 0.5
        assert getattr(detector.model, 'verbose', None) is False

    @patch('store_intel.detection.detector.YOLO')
    def test_detect_returns_detections(self, mock_yolo):
        # Mock YOLO results
        mock_result = MagicMock()
        mock_box1 = MagicMock()
        mock_tensor1_xyxy = MagicMock()
        mock_tensor1_xyxy.cpu.return_value.numpy.return_value = np.array([10.0, 20.0, 30.0, 40.0])
        mock_box1.xyxy = [mock_tensor1_xyxy]
        
        mock_tensor1_conf = MagicMock()
        mock_tensor1_conf.cpu.return_value.numpy.return_value = np.array(0.9)
        mock_box1.conf = [mock_tensor1_conf]
        
        mock_tensor1_cls = MagicMock()
        mock_tensor1_cls.cpu.return_value.numpy.return_value = np.array(0)
        mock_box1.cls = [mock_tensor1_cls]  # Person
        
        mock_box2 = MagicMock()
        mock_tensor2_xyxy = MagicMock()
        mock_tensor2_xyxy.cpu.return_value.numpy.return_value = np.array([50.0, 60.0, 70.0, 80.0])
        mock_box2.xyxy = [mock_tensor2_xyxy]
        
        mock_tensor2_conf = MagicMock()
        mock_tensor2_conf.cpu.return_value.numpy.return_value = np.array(0.8)
        mock_box2.conf = [mock_tensor2_conf]
        
        mock_tensor2_cls = MagicMock()
        mock_tensor2_cls.cpu.return_value.numpy.return_value = np.array(2)
        mock_box2.cls = [mock_tensor2_cls]  # Car
        
        # We assume the model predict call handles filtering, but we test the parsing
        mock_result.boxes = [mock_box1, mock_box2]
        
        mock_model_instance = MagicMock()
        mock_model_instance.predict.return_value = [mock_result]
        mock_yolo.return_value = mock_model_instance

        detector = PersonDetector()
        
        # Dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        detections = detector.detect(frame)
        
        # predict should be called with classes=[0]
        mock_model_instance.predict.assert_called_once_with(frame, classes=[0], conf=0.45, verbose=False)
        
        assert len(detections) == 2
        assert isinstance(detections[0], Detection)
        assert detections[0].bbox == (10.0, 20.0, 30.0, 40.0)
        assert detections[0].confidence == 0.9
        assert detections[0].class_id == 0

    @patch('store_intel.detection.detector.YOLO')
    def test_detect_empty_results(self, mock_yolo):
        mock_result = MagicMock()
        mock_result.boxes = None
        
        mock_model_instance = MagicMock()
        mock_model_instance.predict.return_value = [mock_result]
        mock_yolo.return_value = mock_model_instance

        detector = PersonDetector()
        detections = detector.detect(np.zeros((10, 10, 3)))
        assert len(detections) == 0

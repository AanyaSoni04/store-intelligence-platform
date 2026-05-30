"""
Detection pipeline orchestrator.

Wires together: cv2 → PersonDetector → MultiObjectTracker
    → ZoneManager → VisitorManager → Event Generation
"""

import logging
import json
import time
import cv2
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List

from store_intel.detection.detector import PersonDetector
from store_intel.detection.tracker import MultiObjectTracker
from store_intel.detection.zone_manager import ZoneManager
from store_intel.tracking.visitor import VisitorManager
from store_intel.events.schemas import StoreEvent, EventType

logger = logging.getLogger("store_intel")


class DetectionPipeline:
    """
    End-to-end detection pipeline orchestrator.
    """

    def __init__(
        self,
        video_source: str,
        store_id: str,
        camera_id: str,
        zone_config: str | None = None,
        target_fps: int = 5,
    ):
        self.video_source = video_source
        self.store_id = store_id
        self.camera_id = camera_id
        self.zone_config = zone_config
        self.target_fps = target_fps

        # Initialize components
        self.detector = PersonDetector()
        self.tracker = MultiObjectTracker()
        self.zone_manager = ZoneManager(zone_config)
        self.visitor_manager = VisitorManager(store_id)
        
        self.all_events: List[StoreEvent] = []

    def _map_events_for_camera(self, events: List[StoreEvent]) -> List[StoreEvent]:
        """
        Maps generic ZONE_ENTER / ZONE_EXIT events to camera-specific 
        challenge events.
        """
        mapped_events = []
        for e in events:
            # Basic mapping
            if self.camera_id == "CAM3":
                if e.event_type == EventType.ZONE_ENTER:
                    e.event_type = EventType.ENTRY
                elif e.event_type == EventType.ZONE_EXIT:
                    e.event_type = EventType.EXIT
                    
            elif self.camera_id == "CAM5":
                if e.metadata.get("zone_id") == "billing_queue":
                    if e.event_type == EventType.ZONE_ENTER:
                        e.event_type = EventType.BILLING_QUEUE_JOIN
                    elif e.event_type == EventType.ZONE_EXIT:
                        # We don't know if they abandoned or purchased until we check checkout_counter
                        # For now, just map exit from queue. We'll simplify this logic.
                        e.event_type = EventType.BILLING_QUEUE_ABANDON
                        
                elif e.metadata.get("zone_id") == "checkout_counter":
                    if e.event_type == EventType.ZONE_ENTER:
                        e.event_type = EventType.PURCHASE_PROXY
            
            # Note: For CAM4 STAFF_DETECTED / STAFF_EXCLUSION, we handle that in visitor_manager scoring,
            # but we can explicitly emit it here if a person is flagged.
            mapped_events.append(e)
            
        return mapped_events

    def run(self) -> int:
        """
        Execute the full detection pipeline on a local MP4 file.
        Saves output to data/generated_events.json.
        """
        logger.info(f"Starting pipeline on {self.video_source} for camera {self.camera_id}")
        
        cap = cv2.VideoCapture(self.video_source)
        if not cap.isOpened():
            logger.error(f"Failed to open video source: {self.video_source}")
            return 0
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_skip = int(fps / self.target_fps) if fps > self.target_fps else 1
        
        frame_count = 0
        processed_count = 0
        
        start_time = time.time()
        
        # Start logical time for events (can use real time or video offset)
        base_time = datetime.now(timezone.utc)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            if frame_count % frame_skip != 0:
                continue
                
            processed_count += 1
            
            # Calculate event timestamp based on frame count / video fps
            offset_seconds = frame_count / fps if fps > 0 else 0
            current_timestamp = base_time + timedelta(seconds=offset_seconds)
            
            # 1. Detect
            detections = self.detector.detect(frame)
            
            # 2. Track
            tracked_persons = self.tracker.update(detections)
            
            # 3. Zone & Event Mapping
            for person in tracked_persons:
                # Find zones for this person's centroid
                active_zones = self.zone_manager.check_zones(person.centroid)
                
                # Update visitor state and generate generic zone events
                events = self.visitor_manager.process_zone_hits(
                    track_id=person.track_id,
                    camera_id=self.camera_id,
                    current_zones=active_zones,
                    timestamp=current_timestamp
                )
                
                # Map to camera-specific event types
                mapped_events = self._map_events_for_camera(events)
                
                if mapped_events:
                    for ev in mapped_events:
                        print(f"EVENT GENERATED: {ev.event_type} - Visitor {ev.visitor_id} at {ev.timestamp}")
                    self.all_events.extend(mapped_events)

        cap.release()
        
        end_time = time.time()
        elapsed = end_time - start_time
        achieved_fps = processed_count / elapsed if elapsed > 0 else 0
        
        logger.info(f"Pipeline complete. Processed {processed_count} frames in {elapsed:.2f}s ({achieved_fps:.2f} FPS). Generated {len(self.all_events)} events.")
        
        # Save to JSON
        output_path = Path("data/generated_events.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump([e.model_dump(mode="json") for e in self.all_events], f, indent=2)
            
        logger.info(f"Events saved to {output_path}")
        
        return len(self.all_events)

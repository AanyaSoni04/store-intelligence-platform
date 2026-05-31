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
        self._prev_track_ids: set[int] = set()
        
        self._last_telemetry_time = 0.0
        self._last_telemetry_state = None

    def _emit_telemetry(self, current_track_ids: set[int]):
        """Emit real-time telemetry if 1 second has passed and state has changed."""
        now = time.time()
        if now - self._last_telemetry_time < 1.0:
            return

        # Calculate zone occupancy
        zone_occupancy = {}
        for state in self.visitor_manager._states.values():
            for zone_id in state.active_zones.keys():
                zone_occupancy[zone_id] = zone_occupancy.get(zone_id, 0) + 1

        telemetry_payload = {
            "camera_id": self.camera_id,
            "active_visitors": len(self.visitor_manager._states),
            "active_tracks": len(current_track_ids),
            "zone_occupancy": zone_occupancy,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if telemetry_payload != self._last_telemetry_state:
            try:
                import requests
                requests.post("http://localhost:8000/telemetry", json=telemetry_payload, timeout=2)
                self._last_telemetry_state = telemetry_payload
                self._last_telemetry_time = now
            except Exception as e:
                logger.debug(f"Failed to emit telemetry: {e}")

    def _map_events_for_camera(self, events: List[StoreEvent]) -> List[StoreEvent]:
        """
        Maps generic ZONE_ENTER / ZONE_EXIT events to camera-specific 
        challenge events.
        """
        import uuid
        mapped_events = []
        for e in events:
            # Always keep original event
            mapped_events.append(e)
            
            # Basic mapping
            if self.camera_id == "CAM3":
                if e.event_type in (EventType.ZONE_ENTER, "ZONE_ENTER"):
                    mapped_events.append(e.model_copy(update={"event_type": EventType.ENTRY, "event_id": str(uuid.uuid4())}))
                elif e.event_type in (EventType.ZONE_EXIT, "ZONE_EXIT"):
                    mapped_events.append(e.model_copy(update={"event_type": EventType.EXIT, "event_id": str(uuid.uuid4())}))
                    
            elif self.camera_id == "CAM5":
                if e.metadata.get("zone_id") == "billing_queue":
                    if e.event_type in (EventType.ZONE_ENTER, "ZONE_ENTER"):
                        mapped_events.append(e.model_copy(update={"event_type": EventType.BILLING_QUEUE_JOIN, "event_id": str(uuid.uuid4())}))
                    elif e.event_type == EventType.ZONE_EXIT:
                        # We don't know if they abandoned or purchased until we check checkout_counter
                        # For now, just map exit from queue. We'll simplify this logic.
                        mapped_events.append(e.model_copy(update={"event_type": EventType.BILLING_QUEUE_ABANDON, "event_id": str(uuid.uuid4())}))
                        
                elif e.metadata.get("zone_id") == "checkout_counter":
                    if e.event_type == EventType.ZONE_ENTER:
                        mapped_events.append(e.model_copy(update={"event_type": EventType.PURCHASE_PROXY, "event_id": str(uuid.uuid4())}))
            
            # Map staff detected to both STAFF_DETECTED and STAFF_EXCLUSION
            if e.event_type == EventType.STAFF_DETECTED:
                exclude_event = StoreEvent(
                    store_id=e.store_id,
                    camera_id=e.camera_id,
                    visitor_id=e.visitor_id,
                    event_type=EventType.STAFF_EXCLUSION,
                    timestamp=e.timestamp,
                    confidence=e.confidence,
                    metadata=e.metadata
                )
                mapped_events.append(exclude_event)
            
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
            current_track_ids = {p.track_id for p in tracked_persons}
            
            # Handle lost tracks to generate ZONE_EXIT
            lost_tracks = self._prev_track_ids - current_track_ids
            for track_id in lost_tracks:
                events = self.visitor_manager.process_zone_hits(
                    track_id=track_id,
                    camera_id=self.camera_id,
                    current_zones=[],
                    timestamp=current_timestamp
                )
                self.visitor_manager.remove_track(track_id, current_timestamp)
                mapped_events = self._map_events_for_camera(events)
                if mapped_events:
                    for ev in mapped_events:
                        if ev.event_type in (EventType.ZONE_EXIT, EventType.EXIT):
                            logger.info(f"Generated {ev.event_type.value} event for visitor {ev.visitor_id}")
                    self.all_events.extend(mapped_events)
            
            self._prev_track_ids = current_track_ids
            
            # 3. Zone & Event Mapping
            frame_mapped_events = []
            frame_centroids = {}
            
            for person in tracked_persons:
                frame_centroids[person.track_id] = person.centroid
                
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
                        ev._temp_track_id = person.track_id
                        frame_mapped_events.append(ev)
                        if ev.event_type in (EventType.ZONE_EXIT, EventType.EXIT):
                            logger.info(f"Generated {ev.event_type.value} event for visitor {ev.visitor_id}")
            
            # Spatial Group Clustering for ENTRY events
            self._cluster_entry_events(frame_mapped_events, frame_centroids)

            # Cleanup temp attribute and add to global list
            for ev in frame_mapped_events:
                if hasattr(ev, "_temp_track_id"):
                    delattr(ev, "_temp_track_id")
                self.all_events.append(ev)

            # Emit telemetry
            self._emit_telemetry(current_track_ids)

        cap.release()
        
        # Flush remaining active tracks at end of video
        flush_timestamp = current_timestamp if 'current_timestamp' in locals() else base_time
        for track_id in self._prev_track_ids:
            events = self.visitor_manager.process_zone_hits(
                track_id=track_id,
                camera_id=self.camera_id,
                current_zones=[],
                timestamp=flush_timestamp
            )
            self.visitor_manager.remove_track(track_id, flush_timestamp)
            mapped_events = self._map_events_for_camera(events)
            if mapped_events:
                for ev in mapped_events:
                    if ev.event_type in (EventType.ZONE_EXIT, EventType.EXIT):
                        logger.info(f"Generated {ev.event_type.value} event for visitor {ev.visitor_id}")
                self.all_events.extend(mapped_events)
                
        self._prev_track_ids.clear()
        
        end_time = time.time()
        elapsed = end_time - start_time
        achieved_fps = processed_count / elapsed if elapsed > 0 else 0
        
        logger.info(f"Pipeline complete. Processed {processed_count} frames in {elapsed:.2f}s ({achieved_fps:.2f} FPS). Generated {len(self.all_events)} events.")
        
        # Save to JSON for debugging
        output_path = Path("data/generated_events.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        events_json = [e.model_dump(mode="json") for e in self.all_events]
        with open(output_path, "w") as f:
            json.dump(events_json, f, indent=2)
            
        # Ingest to FastAPI in batches of 500
        import requests
        batch_size = 500
        total_accepted = 0
        
        try:
            for i in range(0, len(events_json), batch_size):
                batch = events_json[i:i + batch_size]
                resp = requests.post(
                    "http://localhost:8000/events/ingest", 
                    json={"events": batch},
                    timeout=10
                )
                if resp.status_code == 202:
                    total_accepted += resp.json().get('accepted', 0)
                else:
                    logger.error(f"Ingestion failed for batch {i//batch_size}: {resp.text}")
                    
            logger.info(f"Ingested {total_accepted} events to database")
        except Exception as e:
            logger.error(f"Could not connect to ingestion API: {e}")
            
        logger.info(f"Events saved to {output_path}")
        
        return len(self.all_events)

    def _cluster_entry_events(self, mapped_events: List[StoreEvent], centroids: dict):
        """Cluster entry events based on spatial proximity."""
        entries = [ev for ev in mapped_events if getattr(ev, 'event_type', None) in (EventType.ENTRY, "ENTRY")]
        for ev in entries:
            group_size = 1
            if not hasattr(ev, '_temp_track_id') or ev._temp_track_id not in centroids:
                continue
            c1 = centroids[ev._temp_track_id]
            for other_ev in entries:
                if ev._temp_track_id != getattr(other_ev, '_temp_track_id', None):
                    c2 = centroids.get(getattr(other_ev, '_temp_track_id', None))
                    if c2:
                        dist = ((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)**0.5
                        if dist < 250:
                            group_size += 1
            if ev.metadata is None:
                ev.metadata = {}
            ev.metadata["group_size"] = group_size

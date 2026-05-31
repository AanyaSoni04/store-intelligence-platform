"""
Visitor identity and state manager.

Responsibilities:
    - Assign persistent visitor_ids to track_ids
    - Maintain state for each visitor (active zones, timestamps)
    - Compute staff_score based on deterministic heuristics
    - Generate zone entry/exit events (Materialization)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from store_intel.events.schemas import StoreEvent, EventType

logger = logging.getLogger("store_intel")


STAFF_SCORE_THRESHOLD = 100


@dataclass
class VisitorState:
    """State of a single visitor currently being tracked."""
    visitor_id: str
    track_id: int
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime | None = None
    active_zones: dict[str, datetime] = field(default_factory=dict)
    visited_zones: set[str] = field(default_factory=set)
    staff_score: int = 0
    is_staff: bool = False
    
    def add_staff_score(self, points: int) -> bool:
        if self.is_staff:
            return False
        self.staff_score += points
        if self.staff_score >= STAFF_SCORE_THRESHOLD:
            self.is_staff = True
            logger.info(f"Visitor {self.visitor_id} flagged as staff (Score: {self.staff_score})")
            return True
        return False


class VisitorManager:
    """
    Manages active visitors, tracks zone transitions, and computes staff heuristic.
    """

    def __init__(self, store_id: str):
        self.store_id = store_id
        self._states: dict[int, VisitorState] = {}
        self.exited_visitors: dict[str, VisitorState] = {}
        self.reentry_window = 300  # seconds
        self.staff_zones = {"stockroom", "behind_counter"}

    def get_or_create(self, track_id: int, timestamp: datetime) -> tuple[VisitorState, bool, str | None]:
        reentered_from = None
        is_new = False
        if track_id not in self._states:
            # Check cache for recent exits
            for vid, old_state in list(self.exited_visitors.items()):
                if old_state.last_seen:
                    gap = (timestamp - old_state.last_seen).total_seconds()
                    if gap <= self.reentry_window:
                        old_state.track_id = track_id
                        self._states[track_id] = old_state
                        self.exited_visitors.pop(vid)
                        reentered_from = vid
                        return old_state, True, reentered_from

            visitor_id = f"v_{uuid4().hex[:12]}"
            self._states[track_id] = VisitorState(visitor_id=visitor_id, track_id=track_id)
            is_new = True
            logger.debug(
                "New visitor assigned",
                extra={"track_id": track_id, "visitor_id": visitor_id},
            )
        return self._states[track_id], is_new, reentered_from

    def remove_track(self, track_id: int, timestamp: datetime) -> None:
        """Remove a track mapping when the track is lost."""
        state = self._states.pop(track_id, None)
        if state:
            state.last_seen = timestamp
            self.exited_visitors[state.visitor_id] = state

    def process_zone_hits(self, track_id: int, camera_id: str, current_zones: list[str], timestamp: datetime) -> list[StoreEvent]:
        """
        Compare current zone hits against active zones to generate Enter/Exit events.
        Also updates the deterministic staff scoring heuristic.
        """
        state, is_new, reentered_from = self.get_or_create(track_id, timestamp)
        events = []
        
        if is_new and reentered_from:
            gap_seconds = (timestamp - state.last_seen).total_seconds() if state.last_seen else 0
            events.append(StoreEvent(
                store_id=self.store_id,
                camera_id=camera_id,
                visitor_id=state.visitor_id,
                event_type=EventType.REENTRY,
                timestamp=timestamp,
                confidence=0.9,
                metadata={"original_visitor_id": reentered_from, "gap_seconds": gap_seconds}
            ))

        current_zones_set = set(current_zones)
        active_zones_set = set(state.active_zones.keys())
        
        # 1. Check for newly entered zones
        entered = current_zones_set - active_zones_set
        for zone_id in entered:
            state.active_zones[zone_id] = timestamp
            
            # Staff Scoring Heuristic: Entering a restricted zone
            if zone_id in self.staff_zones:
                # If this is the very first zone they entered (originating from staff zone)
                points = 50 if not state.visited_zones else 30
                if state.add_staff_score(points):
                    events.append(StoreEvent(
                        store_id=self.store_id,
                        camera_id=camera_id,
                        visitor_id=state.visitor_id,
                        event_type=EventType.STAFF_DETECTED,
                        timestamp=timestamp,
                        confidence=1.0,
                        metadata={"score": state.staff_score}
                    ))
                    
            # Staff Scoring Heuristic: Traverse many zones
            if zone_id not in state.visited_zones:
                state.visited_zones.add(zone_id)
                # If they visit 5+ zones rapidly, they might be restocking
                if len(state.visited_zones) >= 5:
                    if state.add_staff_score(5):
                        events.append(StoreEvent(
                            store_id=self.store_id,
                            camera_id=camera_id,
                            visitor_id=state.visitor_id,
                            event_type=EventType.STAFF_DETECTED,
                            timestamp=timestamp,
                            confidence=1.0,
                            metadata={"score": state.staff_score}
                        ))

            # Generate EVENT
            events.append(StoreEvent(
                store_id=self.store_id,
                camera_id=camera_id,
                visitor_id=state.visitor_id,
                event_type=EventType.ZONE_ENTER,
                timestamp=timestamp,
                confidence=0.9,
                metadata={"zone_id": zone_id}
            ))

        # 2. Check for exited zones
        exited = active_zones_set - current_zones_set
        for zone_id in exited:
            enter_time = state.active_zones.pop(zone_id)
            dwell_seconds = (timestamp - enter_time).total_seconds()
            
            # Generate EVENT
            events.append(StoreEvent(
                store_id=self.store_id,
                camera_id=camera_id,
                visitor_id=state.visitor_id,
                event_type=EventType.ZONE_EXIT,
                timestamp=timestamp,
                confidence=0.9,
                metadata={"zone_id": zone_id, "dwell_seconds": dwell_seconds}
            ))
            
        # 3. Staff Scoring Heuristic: Long dwell time overall
        total_time_seconds = (timestamp - state.first_seen).total_seconds()
        # 2 hours = 7200 seconds -> +10 points. 
        # We can calculate how many 2-hour blocks they've spent.
        blocks_spent = int(total_time_seconds // 7200)
        # Assuming we only add points when they hit a new block, 
        # a simple way is just score = base_score + blocks * 10
        # For simplicity, we just add points based on current time
        # This is a bit naive if called every frame, so we'll just check if they cross a block boundary
        if total_time_seconds > 0 and int(total_time_seconds) % 7200 == 0:
            if state.add_staff_score(10):
                events.append(StoreEvent(
                    store_id=self.store_id,
                    camera_id=camera_id,
                    visitor_id=state.visitor_id,
                    event_type=EventType.STAFF_DETECTED,
                    timestamp=timestamp,
                    confidence=1.0,
                    metadata={"score": state.staff_score}
                ))

        return events

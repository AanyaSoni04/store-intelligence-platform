"""
Zone manager — polygon hit-testing and line-crossing detection.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from shapely.geometry import Point, Polygon, LineString

logger = logging.getLogger("store_intel")


@dataclass
class Zone:
    """A zone or line defined for a camera."""
    zone_id: str
    zone_type: str         # ENTRY_LINE, EXIT_LINE, AISLE, DISPLAY, BILLING, RESTRICTED
    zone_name: str = ""
    points: list = field(default_factory=list)     # list of [x, y] points
    
    # Internal shapely objects
    _polygon: Polygon | None = field(init=False, repr=False, default=None)
    _line: LineString | None = field(init=False, repr=False, default=None)

    def __post_init__(self):
        if not self.points:
            return
            
        if self.zone_type in ("ENTRY_LINE", "EXIT_LINE"):
            if len(self.points) == 2:
                self._line = LineString(self.points)
        else:
            if len(self.points) >= 3:
                self._polygon = Polygon(self.points)


@dataclass
class LineCrossing:
    """Result of a line crossing check."""
    zone_id: str
    direction: str  # "inward" or "outward"


class ZoneManager:
    """
    Manages zone polygons and line-crossing detection for a camera.

    Usage:
        zm = ZoneManager("configs/zones/cam_001.json")
        zone_hits = zm.check_zones((cx, cy))
        crossings = zm.check_line_crossing(prev_centroid, curr_centroid)
    """

    def __init__(self, config_path: str | None = None):
        self.zones: list[Zone] = []
        if config_path:
            self.load_zones(config_path)

    def load_zones(self, config_path: str) -> None:
        """Load zone definitions from a JSON config file."""
        path = Path(config_path)
        if not path.exists():
            logger.warning("Zone config not found", extra={"path": config_path})
            return

        with open(path) as f:
            config = json.load(f)

        for zone_data in config.get("zones", []):
            # Map 'polygon' key to 'points' if present in older configs
            if "polygon" in zone_data and "points" not in zone_data:
                zone_data["points"] = zone_data.pop("polygon")
            
            self.zones.append(Zone(**zone_data))

        logger.info("Zones loaded", extra={"count": len(self.zones), "path": config_path})

    def check_zones(self, centroid: tuple[float, float]) -> list[str]:
        """
        Check which polygon zones contain the given centroid.

        Returns:
            List of zone_ids the centroid is inside.
        """
        p = Point(centroid)
        active_zones = []
        
        for z in self.zones:
            if z._polygon and z._polygon.contains(p):
                active_zones.append(z.zone_id)
                
        return active_zones

    def check_line_crossing(
        self,
        prev_centroid: tuple[float, float],
        curr_centroid: tuple[float, float],
    ) -> list[LineCrossing]:
        """
        Check if movement from prev to curr crosses any entry/exit lines.

        Returns:
            List of LineCrossing results (zone_id + direction).
        """
        if prev_centroid == curr_centroid:
            return []
            
        move_line = LineString([prev_centroid, curr_centroid])
        crossings = []
        
        for z in self.zones:
            if z._line and move_line.intersects(z._line):
                # Calculate cross product to determine direction
                # v1 is the zone line vector
                # v2 is the movement vector
                p1, p2 = z.points[0], z.points[1]
                v1_x = p2[0] - p1[0]
                v1_y = p2[1] - p1[1]
                
                v2_x = curr_centroid[0] - prev_centroid[0]
                v2_y = curr_centroid[1] - prev_centroid[1]
                
                # 2D cross product: v1_x*v2_y - v1_y*v2_x
                cross = v1_x * v2_y - v1_y * v2_x
                
                # By convention, assume cross > 0 is inward relative to how the line is drawn
                direction = "inward" if cross > 0 else "outward"
                
                crossings.append(LineCrossing(zone_id=z.zone_id, direction=direction))
                
        return crossings

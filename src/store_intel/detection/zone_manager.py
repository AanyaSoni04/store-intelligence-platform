"""
Zone manager — polygon hit-testing and line-crossing detection.

TODO: Implement ZoneManager class with:
    - load_zones(config_path): load polygon definitions from JSON
    - check_zones(centroid): return list of zone_ids the point is inside
    - check_line_crossing(prev_centroid, curr_centroid): detect entry/exit line crossings
    - Zone types: ENTRY_LINE, EXIT_LINE, AISLE, DISPLAY, BILLING, RESTRICTED

Zone config JSON format (per camera):
    {
        "camera_id": "cam_001",
        "zones": [
            {
                "zone_id": "main_entrance",
                "zone_type": "ENTRY_LINE",
                "points": [[x1,y1], [x2,y2]]
            },
            {
                "zone_id": "electronics",
                "zone_type": "AISLE",
                "zone_name": "Electronics Aisle",
                "polygon": [[x1,y1], [x2,y2], [x3,y3], ...]
            }
        ]
    }
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("store_intel")


@dataclass
class Zone:
    """A zone or line defined for a camera."""
    zone_id: str
    zone_type: str         # ENTRY_LINE, EXIT_LINE, AISLE, DISPLAY, BILLING, RESTRICTED
    zone_name: str = ""
    polygon: list = field(default_factory=list)   # list of [x, y] points
    points: list = field(default_factory=list)     # for lines: exactly 2 points


@dataclass
class LineCrossing:
    """Result of a line crossing check."""
    zone_id: str
    direction: str  # "inward" or "outward"


class ZoneManager:
    """
    Manages zone polygons and line-crossing detection for a camera.

    TODO: Implement using Shapely for polygon operations.

    Usage:
        zm = ZoneManager("configs/zones/cam_001.json")
        zone_hits = zm.check_zones((cx, cy))
        crossings = zm.check_line_crossing(prev_centroid, curr_centroid)
    """

    def __init__(self, config_path: str | None = None):
        self.zones: list[Zone] = []
        # TODO: Initialize Shapely polygon objects
        if config_path:
            self.load_zones(config_path)

    def load_zones(self, config_path: str) -> None:
        """
        Load zone definitions from a JSON config file.

        TODO: Implement:
            - Parse JSON file
            - Create Shapely Polygon objects for polygon zones
            - Create Shapely LineString objects for line zones
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning("Zone config not found", extra={"path": config_path})
            return

        with open(path) as f:
            config = json.load(f)

        for zone_data in config.get("zones", []):
            self.zones.append(Zone(**zone_data))

        logger.info("Zones loaded", extra={"count": len(self.zones), "path": config_path})

    def check_zones(self, centroid: tuple[float, float]) -> list[str]:
        """
        Check which polygon zones contain the given centroid.

        TODO: Implement using Shapely Point.within(Polygon).

        Returns:
            List of zone_ids the centroid is inside.
        """
        # TODO: Implement polygon containment checks
        raise NotImplementedError("Zone containment check not yet implemented")

    def check_line_crossing(
        self,
        prev_centroid: tuple[float, float],
        curr_centroid: tuple[float, float],
    ) -> list[LineCrossing]:
        """
        Check if movement from prev to curr crosses any entry/exit lines.

        TODO: Implement using cross-product sign to determine direction.

        Returns:
            List of LineCrossing results (zone_id + direction).
        """
        # TODO: Implement line crossing detection
        raise NotImplementedError("Line crossing detection not yet implemented")

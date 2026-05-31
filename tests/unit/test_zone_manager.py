"""
Unit tests for ZoneManager.
"""
from store_intel.detection.zone_manager import ZoneManager


class TestZoneManager:
    """Tests for zone polygon and line crossing logic."""

    def test_load_zones(self):
        """Test that zones can be loaded from a JSON file."""
        zm = ZoneManager("configs/zones/cam_001.json")
        assert len(zm.zones) >= 1
        # Make sure polygon logic initialized
        first_polygon = next(z for z in zm.zones if z.zone_type == "DISPLAY" or z.zone_type == "AISLE")
        assert first_polygon._polygon is not None

    def test_point_inside_polygon(self):
        zm = ZoneManager()
        # Mocking a simple zone
        from store_intel.detection.zone_manager import Zone
        zm.zones.append(Zone(zone_id="test_zone", zone_type="AISLE", points=[[0, 0], [10, 0], [10, 10], [0, 10]]))
        
        # Point inside
        hits = zm.check_zones((5, 5))
        assert "test_zone" in hits
        
        # Point outside
        hits2 = zm.check_zones((15, 15))
        assert "test_zone" not in hits2

    def test_line_crossing(self):
        from store_intel.detection.zone_manager import Zone
        zm = ZoneManager()
        zm.zones.append(Zone(zone_id="gate", zone_type="ENTRY_LINE", points=[[0, 5], [10, 5]]))
        
        # Crossing upward (0,0) to (0,10)
        crossings = zm.check_line_crossing((5, 0), (5, 10))
        assert len(crossings) == 1
        assert crossings[0].zone_id == "gate"
        assert crossings[0].direction == "inward"
        
        # Crossing downward (0,10) to (0,0)
        crossings2 = zm.check_line_crossing((5, 10), (5, 0))
        assert len(crossings2) == 1
        assert crossings2[0].zone_id == "gate"
        assert crossings2[0].direction == "outward"
        
        # No crossing (parallel)
        crossings3 = zm.check_line_crossing((0, 0), (10, 0))
        assert len(crossings3) == 0

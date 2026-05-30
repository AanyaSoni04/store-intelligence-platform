"""
Detection pipeline orchestrator.

Wires together: FrameDecoder → PersonDetector → MultiObjectTracker
    → ZoneManager → EventMaterializer → DB write

TODO: Implement DetectionPipeline class with:
    - __init__(video_source, store_id, camera_id, zone_config)
    - run(): execute the full pipeline, writing events to the database
    - process_frame(frame): single-frame processing for testing
"""

import logging

logger = logging.getLogger("store_intel")


class DetectionPipeline:
    """
    End-to-end detection pipeline orchestrator.

    TODO: Implement the full pipeline:
        1. Decode frames from video source
        2. Run person detection (YOLOv8)
        3. Track persons across frames (ByteTrack)
        4. Check zone hits and line crossings
        5. Feed into event materializer FSM
        6. Write emitted events to database

    Usage:
        pipeline = DetectionPipeline(
            video_source="path/to/video.mp4",
            store_id="store_001",
            camera_id="cam_001",
            zone_config="configs/zones/cam_001.json",
        )
        pipeline.run()
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

        # TODO: Initialize pipeline components:
        # self.decoder = FrameDecoder(video_source, target_fps)
        # self.detector = PersonDetector()
        # self.tracker = MultiObjectTracker()
        # self.zone_manager = ZoneManager(zone_config)
        # self.materializer = EventMaterializer(store_id, camera_id)

    def run(self) -> int:
        """
        Execute the full detection pipeline.

        TODO: Implement:
            - Iterate over decoded frames
            - Detect → Track → Zone check → Materialize events
            - Write events to database
            - Return total event count

        Returns:
            Number of events generated.
        """
        raise NotImplementedError("Detection pipeline not yet implemented")

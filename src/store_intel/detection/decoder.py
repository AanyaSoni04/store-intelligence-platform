"""
Frame decoder — reads video files or RTSP streams via OpenCV.

TODO: Implement FrameDecoder class with:
    - __init__(source, target_fps): accepts file path or RTSP URL
    - __iter__: yields (frame_index, timestamp, numpy_array) tuples
    - Skip frames to achieve target_fps
    - Handle corrupt frames gracefully (skip + log)
    - Support context manager for clean resource cleanup
"""

import logging

logger = logging.getLogger("store_intel")


class FrameDecoder:
    """
    Decodes video frames from a file or RTSP stream.

    TODO: Implement using cv2.VideoCapture.

    Usage:
        decoder = FrameDecoder("path/to/video.mp4", target_fps=5)
        for frame_idx, timestamp, frame in decoder:
            # process frame
    """

    def __init__(self, source: str, target_fps: int = 5):
        self.source = source
        self.target_fps = target_fps
        # TODO: Initialize cv2.VideoCapture
        # TODO: Read source FPS, compute frame skip interval

    def __iter__(self):
        # TODO: Yield (frame_index, timestamp, numpy_array) tuples
        raise NotImplementedError("FrameDecoder not yet implemented")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: Release cv2.VideoCapture resource
        pass

import pytest
import numpy as np
from store_intel.detection.decoder import FrameDecoder

def test_decoder():
    decoder = FrameDecoder("mock.mp4")
    assert decoder.source == "mock.mp4"
    assert decoder.target_fps == 5
    
    # We can't really test open() without a real video, but we can test the class exists and handles basics

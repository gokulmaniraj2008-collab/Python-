import tempfile
import unittest
from pathlib import Path

import numpy as np

from creative_studio.video import write_video


class VideoTests(unittest.TestCase):
    def test_rejects_empty_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                write_video([], Path(directory) / "empty.mp4")

    def test_rejects_invalid_fps(self):
        with self.assertRaises(ValueError):
            write_video([np.zeros((16, 16, 3), dtype=np.uint8)], "unused.mp4", fps=0)

    def test_rejects_invalid_frame_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            frame = np.zeros((16, 16), dtype=np.uint8)
            with self.assertRaises(ValueError):
                write_video([frame], Path(directory) / "invalid.mp4")


if __name__ == "__main__":
    unittest.main()

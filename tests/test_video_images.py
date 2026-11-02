"""Tests for image-sequence video assembly validation."""

import tempfile
import unittest
from pathlib import Path
from PIL import Image

from creative_studio.video import create_video_from_images


class ImageSequenceVideoTests(unittest.TestCase):
    def test_empty_image_sequence_is_rejected(self):
        with self.assertRaises(ValueError):
            create_video_from_images([], "unused.mp4")

    def test_mixed_image_dimensions_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / "01.png"
            second = Path(folder) / "02.png"
            Image.new("RGB", (16, 16)).save(first)
            Image.new("RGB", (20, 16)).save(second)
            with self.assertRaises(ValueError):
                create_video_from_images([first, second], Path(folder) / "out.mp4")


if __name__ == "__main__":
    unittest.main()

import unittest
import tempfile
from pathlib import Path

from PIL import Image

from creative_studio.animation import Timeline, ease, render_ken_burns


class TimelineTests(unittest.TestCase):
    def test_frame_count_and_time(self):
        timeline = Timeline(fps=30, duration_seconds=2)
        self.assertEqual(timeline.frame_count, 60)
        self.assertAlmostEqual(timeline.time_at(15), 0.5)

    def test_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            Timeline(fps=0)
        with self.assertRaises(IndexError):
            Timeline().time_at(-1)

    def test_short_timeline_has_one_frame(self):
        self.assertEqual(Timeline(fps=1, duration_seconds=0.1).frame_count, 1)

    def test_easing_curves(self):
        self.assertAlmostEqual(ease(0.5, "linear"), 0.5)
        self.assertAlmostEqual(ease(0.5, "ease-in"), 0.25)
        self.assertAlmostEqual(ease(0.5, "ease-out"), 0.75)
        self.assertAlmostEqual(ease(0.5, "ease-in-out"), 0.5)

    def test_invalid_easing_is_rejected(self):
        with self.assertRaises(ValueError):
            ease(0.5, "bounce")

    def test_render_rejects_zoom_below_one(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.png"
            Image.new("RGB", (16, 16)).save(source)
            with self.assertRaises(ValueError):
                render_ken_burns(source, Path(folder) / "out.mp4", start_zoom=0.8)

    def test_render_rejects_invalid_focus(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.png"
            Image.new("RGB", (16, 16)).save(source)
            with self.assertRaises(ValueError):
                render_ken_burns(source, Path(folder) / "out.mp4", start_focus=(2, 0.5))


if __name__ == "__main__":
    unittest.main()

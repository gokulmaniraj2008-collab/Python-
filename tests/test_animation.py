import unittest

from creative_studio.animation import Timeline


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


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from creative_studio.image import create_thumbnail


class ImageTests(unittest.TestCase):
    def test_thumbnail_is_created_within_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            target = root / "nested" / "thumb.png"
            Image.new("RGB", (1200, 600), "white").save(source)
            result = create_thumbnail(source, target, (300, 300))
            self.assertEqual(result, target)
            with Image.open(target) as image:
                self.assertEqual(image.size, (300, 150))

    def test_rejects_invalid_size(self):
        with self.assertRaises(ValueError):
            create_thumbnail("unused.png", "unused-out.png", (0, 10))


if __name__ == "__main__":
    unittest.main()

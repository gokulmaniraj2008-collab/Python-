import unittest
from pathlib import Path


class StudioPageTests(unittest.TestCase):
    def test_mobile_studio_page_has_core_workflows(self):
        page = Path(__file__).resolve().parents[1] / "studio.html"
        html = page.read_text(encoding="utf-8")
        for marker in (
            'id="prompt"', 'id="source-image"', 'id="make-image"',
            'id="make-animation"', 'creative_studio generate-image',
            'creative_studio animate-image', 'HF_TOKEN',
        ):
            self.assertIn(marker, html)

    def test_studio_page_does_not_embed_a_secret(self):
        page = Path(__file__).resolve().parents[1] / "studio.html"
        html = page.read_text(encoding="utf-8")
        self.assertNotIn("hf_", html)
        self.assertNotIn("HF_TOKEN=", html)


if __name__ == "__main__":
    unittest.main()

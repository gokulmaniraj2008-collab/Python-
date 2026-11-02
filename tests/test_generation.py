"""Tests for provider-driven generation workflows."""

import tempfile
import unittest
from pathlib import Path

from creative_studio.generation import generate_image
from creative_studio.providers.huggingface import HuggingFaceImageProvider


class FakeProvider:
    def generate(self, prompt: str, output: str | Path) -> Path:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(prompt, encoding="utf-8")
        return path


class GenerationTests(unittest.TestCase):
    def test_generate_image_delegates_to_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "image.txt"
            result = generate_image(FakeProvider(), "  tiny robot  ", target)
            self.assertEqual(result.read_text(encoding="utf-8"), "tiny robot")

    def test_empty_prompt_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_image(FakeProvider(), "  ", "unused.png")

    def test_huggingface_provider_requires_token(self):
        with self.assertRaises(ValueError):
            HuggingFaceImageProvider(token="")

    def test_huggingface_provider_validates_model_and_timeout(self):
        with self.assertRaises(ValueError):
            HuggingFaceImageProvider(token="test", model=" ")
        with self.assertRaises(ValueError):
            HuggingFaceImageProvider(token="test", timeout=0)


if __name__ == "__main__":
    unittest.main()

"""Provider contracts used by creative generation workflows."""

from pathlib import Path
from typing import Protocol


class ImageProvider(Protocol):
    """A service capable of turning a text prompt into an image file."""

    def generate(self, prompt: str, output: str | Path) -> Path:
        """Generate an image from prompt and save it to output."""

"""High-level generation workflows built on provider interfaces."""

from pathlib import Path
from creative_studio.providers.base import ImageProvider


def generate_image(provider: ImageProvider, prompt: str,
                   output: str | Path) -> Path:
    """Validate a prompt and delegate image creation to a provider."""
    if not prompt or not prompt.strip():
        raise ValueError("prompt must not be empty")
    return provider.generate(prompt.strip(), output)

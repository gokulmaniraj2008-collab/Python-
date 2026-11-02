"""Optional remote and local generation providers."""

from creative_studio.providers.base import ImageProvider
from creative_studio.providers.huggingface import HuggingFaceImageProvider

__all__ = ["ImageProvider", "HuggingFaceImageProvider"]

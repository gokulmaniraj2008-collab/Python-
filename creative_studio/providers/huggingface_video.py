"""Hugging Face Inference Providers text-to-video adapter.

Requires the optional huggingface_hub package and a user-supplied HF_TOKEN.
The token is read at runtime and is never returned to clients or written to disk.
"""
from __future__ import annotations

import os


class HuggingFaceVideoProvider:
    """Generate MP4 bytes through a Hugging Face routed inference provider."""

    def __init__(self, token: str | None = None, model: str | None = None,
                 provider: str | None = None, timeout: int = 600) -> None:
        self.token = token or os.getenv("HF_TOKEN")
        if not self.token:
            raise ValueError("HF_TOKEN is required; set it as a server-side secret")
        self.model = (model or os.getenv(
            "HF_VIDEO_MODEL", "Wan-AI/Wan2.2-TI2V-5B"
        )).strip()
        self.provider = (provider or os.getenv("HF_VIDEO_PROVIDER", "fal-ai")).strip()
        if not self.model or not self.provider:
            raise ValueError("HF_VIDEO_MODEL and HF_VIDEO_PROVIDER must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.timeout = timeout

    def generate(self, prompt: str, duration_seconds: int = 5,
                 aspect_ratio: str = "16:9") -> bytes:
        prompt = prompt.strip()
        if not prompt or len(prompt) > 2000:
            raise ValueError("prompt must contain 1–2000 characters")
        if duration_seconds not in {5, 8, 10, 15}:
            raise ValueError("duration_seconds must be 5, 8, 10, or 15")
        if aspect_ratio not in {"16:9", "9:16", "1:1"}:
            raise ValueError("aspect_ratio must be 16:9, 9:16, or 1:1")

        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError(
                "Video dependencies are missing. Install requirements-video.txt."
            ) from exc

        client = InferenceClient(
            provider=self.provider,
            api_key=self.token,
            timeout=self.timeout,
        )
        # Wan-family text-to-video requests accept frame count. Aspect ratio is
        # retained as job metadata; final dimensions are model/provider-defined.
        video = client.text_to_video(
            prompt,
            model=self.model,
            num_frames=duration_seconds * 16 + 1,
        )
        content = bytes(video)
        if len(content) < 12 or b"ftyp" not in content[:32]:
            raise RuntimeError("The inference provider did not return a valid MP4 payload")
        return content

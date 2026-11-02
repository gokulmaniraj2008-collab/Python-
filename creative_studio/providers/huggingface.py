"""Hugging Face Inference Providers image-generation adapter.

The provider is optional and requires a user-supplied HF_TOKEN. Model access,
provider availability, quotas, and pricing are controlled by Hugging Face.
"""

import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class HuggingFaceImageProvider:
    """Generate an image through the Hugging Face inference router."""

    def __init__(self, token: str | None = None,
                 model: str = "black-forest-labs/FLUX.1-schnell",
                 timeout: int = 180) -> None:
        self.token = token or os.getenv("HF_TOKEN")
        if not self.token:
            raise ValueError("HF_TOKEN is required; set it as an environment secret")
        if not model.strip():
            raise ValueError("model must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.model = model.strip()
        self.timeout = timeout

    def generate(self, prompt: str, output: str | Path) -> Path:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("prompt must not be empty")
        if len(prompt) > 2000:
            raise ValueError("prompt must be 2000 characters or fewer")

        endpoint = (
            "https://router.huggingface.co/hf-inference/models/"
            + quote(self.model, safe="/")
        )
        request = Request(
            endpoint,
            data=__import__("json").dumps({"inputs": prompt}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "image/*",
                "User-Agent": "python-creative-ai-studio/0.2",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                image_bytes = response.read()
        except HTTPError as exc:
            detail = exc.read(500).decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Hugging Face request failed ({exc.code}): {detail}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach Hugging Face: {exc.reason}") from exc

        if not content_type.lower().startswith("image/"):
            preview = image_bytes[:300].decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Expected an image response, received {content_type or 'unknown'}: {preview}"
            )
        if not image_bytes:
            raise RuntimeError("The image provider returned an empty response")

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)
        return output_path

"""Provider-neutral asynchronous text-to-video jobs.

The adapter expects a small REST contract:
POST /jobs with {prompt, duration_seconds, aspect_ratio} -> {id, status}
GET /jobs/{id} -> {id, status, video_url?, error?}
The provider API key is read only from VIDEO_API_KEY and is never persisted.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


class VideoGenerationError(RuntimeError):
    """Raised when a remote video job cannot be completed."""


@dataclass(frozen=True)
class VideoJob:
    job_id: str
    status: str
    video_url: str | None = None
    error: str | None = None


class HTTPVideoProvider:
    """Connect to a video API that implements the documented job contract."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 timeout: int = 30) -> None:
        self.base_url = (base_url or os.getenv("VIDEO_API_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("VIDEO_API_KEY")
        if not self.base_url or not self.api_key:
            raise ValueError("VIDEO_API_URL and VIDEO_API_KEY are required environment variables")
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("VIDEO_API_URL must be an HTTPS URL without embedded credentials")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.timeout = timeout

    def _request_json(self, url: str, method: str = "GET",
                      payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url, data=data, method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "python-creative-ai-studio/0.5",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read(1_000_001)
        except HTTPError as exc:
            detail = exc.read(300).decode("utf-8", errors="replace")
            raise VideoGenerationError(f"Video provider returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise VideoGenerationError(f"Could not reach video provider: {exc.reason}") from exc
        if len(body) > 1_000_000:
            raise VideoGenerationError("Video provider JSON response exceeded 1 MB")
        try:
            result = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise VideoGenerationError("Video provider returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise VideoGenerationError("Video provider response must be a JSON object")
        return result

    def submit(self, prompt: str, duration_seconds: int = 5,
               aspect_ratio: str = "16:9") -> VideoJob:
        prompt = prompt.strip()
        if not prompt or len(prompt) > 2000:
            raise ValueError("prompt must contain 1–2000 characters")
        if not 1 <= duration_seconds <= 120:
            raise ValueError("duration_seconds must be between 1 and 120")
        if aspect_ratio not in {"16:9", "9:16", "1:1"}:
            raise ValueError("aspect_ratio must be 16:9, 9:16, or 1:1")
        data = self._request_json(
            f"{self.base_url}/jobs", "POST",
            {"prompt": prompt, "duration_seconds": duration_seconds,
             "aspect_ratio": aspect_ratio},
        )
        return self._parse_job(data)

    def get_job(self, job_id: str) -> VideoJob:
        if not job_id or len(job_id) > 200:
            raise ValueError("job_id must contain 1–200 characters")
        data = self._request_json(f"{self.base_url}/jobs/{quote(job_id, safe='')}")
        return self._parse_job(data)

    @staticmethod
    def _parse_job(data: dict) -> VideoJob:
        job_id = data.get("id")
        status = data.get("status")
        if not isinstance(job_id, str) or not job_id.strip():
            raise VideoGenerationError("Video provider response is missing a job id")
        if status not in {"queued", "processing", "completed", "failed"}:
            raise VideoGenerationError("Video provider returned an unsupported job status")
        video_url = data.get("video_url")
        if video_url is not None:
            parsed = urlparse(video_url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise VideoGenerationError("Provider video_url must be an HTTPS URL")
        error = data.get("error")
        return VideoJob(job_id=job_id, status=status, video_url=video_url,
                        error=str(error)[:500] if error else None)

    def download(self, job: VideoJob, output: str | Path) -> Path:
        if job.status != "completed" or not job.video_url:
            raise VideoGenerationError("Completed job does not contain a video_url")
        # Deliberately do not forward the provider API key to the CDN URL.
        request = Request(job.video_url, headers={"User-Agent": "python-creative-ai-studio/0.5"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                content = response.read(250_000_001)
        except (HTTPError, URLError) as exc:
            raise VideoGenerationError("Could not download the generated video") from exc
        if content_type and not (content_type.startswith("video/") or
                                 content_type == "application/octet-stream"):
            raise VideoGenerationError("Video URL did not return a video content type")
        if not content or len(content) > 250_000_000:
            raise VideoGenerationError("Video download is empty or exceeds the 250 MB safety limit")
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path


def save_job_record(job: VideoJob, jobs_dir: str | Path = "outputs/video-jobs") -> Path:
    """Persist non-secret job metadata for a local history/gallery workflow."""
    folder = Path(jobs_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{quote(job.job_id, safe='')}.json"
    path.write_text(json.dumps(asdict(job), indent=2), encoding="utf-8")
    return path


def generate_video(provider: HTTPVideoProvider, prompt: str, output: str | Path,
                   duration_seconds: int = 5, aspect_ratio: str = "16:9",
                   poll_interval: float = 5.0, max_wait_seconds: float = 900.0,
                   jobs_dir: str | Path = "outputs/video-jobs") -> Path:
    """Submit, poll, record, and download a video job."""
    if poll_interval < 0 or max_wait_seconds <= 0:
        raise ValueError("poll_interval must be non-negative and max_wait_seconds positive")
    job = provider.submit(prompt, duration_seconds, aspect_ratio)
    save_job_record(job, jobs_dir)
    deadline = time.monotonic() + max_wait_seconds
    while job.status in {"queued", "processing"}:
        if time.monotonic() >= deadline:
            raise VideoGenerationError(f"Timed out waiting for video job {job.job_id}")
        if poll_interval:
            time.sleep(poll_interval)
        job = provider.get_job(job.job_id)
        save_job_record(job, jobs_dir)
    if job.status == "failed":
        raise VideoGenerationError(job.error or f"Video job {job.job_id} failed")
    result = provider.download(job, output)
    save_job_record(job, jobs_dir)
    return result

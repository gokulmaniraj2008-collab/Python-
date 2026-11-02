"""Persistent job tracking and background execution for text-to-video."""
from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from creative_studio.providers.huggingface_video import HuggingFaceVideoProvider


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class VideoJobManager:
    """SQLite-backed job history with a bounded in-process worker pool."""

    def __init__(self, database: str | Path = "outputs/video-jobs.sqlite3",
                 output_dir: str | Path = "outputs/videos",
                 provider_factory: Callable[[], object] | None = None,
                 max_workers: int = 1) -> None:
        if max_workers < 1 or max_workers > 4:
            raise ValueError("max_workers must be between 1 and 4")
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.provider_factory = provider_factory or HuggingFaceVideoProvider
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="video-job")
        self.lock = threading.Lock()
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS video_jobs (
                    id TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    aspect_ratio TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    output_name TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Jobs executing in a previous process cannot resume automatically.
            db.execute(
                "UPDATE video_jobs SET status='failed', error=?, updated_at=? "
                "WHERE status IN ('queued','processing')",
                ("Backend restarted before this job completed; submit it again.", _now()),
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    def submit(self, prompt: str, duration_seconds: int = 5,
               aspect_ratio: str = "16:9") -> dict:
        prompt = prompt.strip()
        if not prompt or len(prompt) > 2000:
            raise ValueError("prompt must contain 1–2000 characters")
        if duration_seconds not in {5, 8, 10, 15}:
            raise ValueError("duration_seconds must be 5, 8, 10, or 15")
        if aspect_ratio not in {"16:9", "9:16", "1:1"}:
            raise ValueError("aspect_ratio must be 16:9, 9:16, or 1:1")
        job_id = uuid.uuid4().hex
        now = _now()
        with self._connect() as db:
            db.execute(
                "INSERT INTO video_jobs VALUES (?, ?, ?, ?, 'queued', NULL, NULL, ?, ?)",
                (job_id, prompt, duration_seconds, aspect_ratio, now, now),
            )
        self.executor.submit(self._run, job_id, prompt, duration_seconds, aspect_ratio)
        return self.get(job_id)

    def _set_status(self, job_id: str, status: str, error: str | None = None,
                    output_name: str | None = None) -> None:
        with self._connect() as db:
            db.execute(
                "UPDATE video_jobs SET status=?, error=?, output_name=?, updated_at=? WHERE id=?",
                (status, error, output_name, _now(), job_id),
            )

    def _run(self, job_id: str, prompt: str, duration_seconds: int,
             aspect_ratio: str) -> None:
        self._set_status(job_id, "processing")
        try:
            provider = self.provider_factory()
            content = provider.generate(prompt, duration_seconds, aspect_ratio)
            if not isinstance(content, (bytes, bytearray)) or len(content) < 12 or b"ftyp" not in content[:32]:
                raise RuntimeError("Provider response is not a valid MP4 file")
            output_name = f"{job_id}.mp4"
            destination = self.output_dir / output_name
            temporary = destination.with_suffix(".mp4.tmp")
            temporary.write_bytes(content)
            temporary.replace(destination)
            self._set_status(job_id, "completed", output_name=output_name)
        except Exception as exc:
            message = str(exc).replace(os.getenv("HF_TOKEN", "\0"), "[redacted]")[:500]
            self._set_status(job_id, "failed", error=message or "Video generation failed")

    def get(self, job_id: str) -> dict:
        if not job_id or len(job_id) != 32 or any(c not in "0123456789abcdef" for c in job_id):
            raise ValueError("invalid job id")
        with self._connect() as db:
            row = db.execute("SELECT * FROM video_jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError("job not found")
        result = dict(row)
        result.pop("output_name", None)
        result.pop("prompt", None)
        return result

    def video_path(self, job_id: str) -> Path:
        # Validate existence and ownership via the database, not user path input.
        self.get(job_id)
        with self._connect() as db:
            row = db.execute(
                "SELECT status, output_name FROM video_jobs WHERE id=?", (job_id,)
            ).fetchone()
        if row["status"] != "completed" or not row["output_name"]:
            raise ValueError("video is not ready")
        path = self.output_dir / row["output_name"]
        if not path.is_file():
            raise FileNotFoundError("video output is missing")
        return path

    def close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=False)

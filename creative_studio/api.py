"""Small authenticated HTTP API for the Creative Studio video worker.

Run with: python -m creative_studio.api
This is a separate Python service; the static Vercel frontend connects to its
public HTTPS URL. Keep HF_TOKEN and VIDEO_API_ACCESS_KEY on the server only.
"""
from __future__ import annotations

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from creative_studio.video_jobs import VideoJobManager


def make_handler(manager: VideoJobManager, access_key: str,
                 allowed_origins: set[str]):
    class Handler(BaseHTTPRequestHandler):
        server_version = "CreativeStudioAPI/0.6"

        def log_message(self, fmt: str, *args) -> None:
            # Avoid logging headers, prompt text, or credentials.
            super().log_message(fmt, *args)

        def _cors(self) -> None:
            origin = self.headers.get("Origin", "")
            if origin in allowed_origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Max-Age", "600")

        def _json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        def _authorized(self) -> bool:
            supplied = self.headers.get("Authorization", "")
            expected = f"Bearer {access_key}"
            return hmac.compare_digest(supplied, expected)

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/health":
                self._json(200, {"ok": True, "service": "creative-studio-video"})
                return
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            parts = path.strip("/").split("/")
            if len(parts) not in {2, 3} or parts[0] != "jobs":
                self._json(404, {"error": "not found"})
                return
            try:
                job_id = unquote(parts[1])
                job = manager.get(job_id)
                if len(parts) == 2:
                    if job["status"] == "completed":
                        job["video_url"] = f"/jobs/{job_id}/video"
                    self._json(200, job)
                    return
                if parts[2] != "video":
                    self._json(404, {"error": "not found"})
                    return
                video = manager.video_path(job_id)
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(video.stat().st_size))
                self.send_header("Content-Disposition", f'inline; filename="{job_id}.mp4"')
                self._cors()
                self.end_headers()
                with video.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        self.wfile.write(chunk)
            except KeyError:
                self._json(404, {"error": "job not found"})
            except (ValueError, FileNotFoundError) as exc:
                self._json(409, {"error": str(exc)})

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/jobs":
                self._json(404, {"error": "not found"})
                return
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._json(400, {"error": "invalid content length"})
                return
            if length < 1 or length > 16_384:
                self._json(413, {"error": "request body must be 1–16384 bytes"})
                return
            try:
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("JSON body must be an object")
                job = manager.submit(
                    payload.get("prompt", ""),
                    int(payload.get("duration_seconds", 5)),
                    payload.get("aspect_ratio", "16:9"),
                )
                self._json(202, job)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self._json(400, {"error": str(exc)[:300]})

    return Handler


def main() -> int:
    access_key = os.getenv("VIDEO_API_ACCESS_KEY", "")
    if len(access_key) < 24:
        raise SystemExit("Set VIDEO_API_ACCESS_KEY to a random secret of at least 24 characters.")
    host = os.getenv("VIDEO_API_HOST", "127.0.0.1")
    port = int(os.getenv("VIDEO_API_PORT", "8787"))
    origins = {
        item.strip() for item in os.getenv(
            "VIDEO_CORS_ORIGINS",
            "http://localhost:8000,http://127.0.0.1:8000",
        ).split(",") if item.strip()
    }
    manager = VideoJobManager(
        database=os.getenv("VIDEO_JOBS_DB", "outputs/video-jobs.sqlite3"),
        output_dir=os.getenv("VIDEO_OUTPUT_DIR", "outputs/videos"),
    )
    server = ThreadingHTTPServer((host, port), make_handler(manager, access_key, origins))
    print(f"Creative Studio video API listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        manager.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

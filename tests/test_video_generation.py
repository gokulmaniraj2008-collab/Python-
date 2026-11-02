import json
import tempfile
import unittest
from pathlib import Path

from creative_studio.video_generation import (
    HTTPVideoProvider, VideoGenerationError, VideoJob, generate_video, save_job_record,
)


class VideoGenerationTests(unittest.TestCase):
    def test_requires_https_and_secrets(self):
        with self.assertRaises(ValueError):
            HTTPVideoProvider("http://example.com", "secret")
        with self.assertRaises(ValueError):
            HTTPVideoProvider("https://example.com", "")

    def test_submit_validates_prompt_and_shape(self):
        provider = HTTPVideoProvider("https://video.example/api", "secret")
        with self.assertRaises(ValueError):
            provider.submit(" ")
        with self.assertRaises(ValueError):
            provider.submit("a prompt", aspect_ratio="4:3")

    def test_parse_job_rejects_insecure_video_url(self):
        with self.assertRaises(VideoGenerationError):
            HTTPVideoProvider._parse_job({
                "id": "abc", "status": "completed", "video_url": "http://bad.example/v.mp4"
            })

    def test_job_record_never_contains_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = save_job_record(VideoJob("job-1", "processing"), directory)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved, {"job_id": "job-1", "status": "processing",
                                     "video_url": None, "error": None})
            self.assertNotIn("secret", path.read_text(encoding="utf-8"))

    def test_generation_polls_and_downloads(self):
        class FakeProvider:
            def __init__(self):
                self.calls = 0
            def submit(self, prompt, duration_seconds, aspect_ratio):
                return VideoJob("job-2", "queued")
            def get_job(self, job_id):
                self.calls += 1
                return VideoJob("job-2", "completed", "https://cdn.example/video.mp4")
            def download(self, job, output):
                target = Path(output)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"fake-mp4")
                return target

        with tempfile.TemporaryDirectory() as directory:
            provider = FakeProvider()
            result = generate_video(provider, "a film", Path(directory) / "clip.mp4",
                                    poll_interval=0, jobs_dir=Path(directory) / "jobs")
            self.assertTrue(result.exists())
            self.assertEqual(provider.calls, 1)
            self.assertTrue((Path(directory) / "jobs" / "job-2.json").exists())


if __name__ == "__main__":
    unittest.main()

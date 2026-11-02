import tempfile
import time
import unittest
from pathlib import Path

from creative_studio.video_jobs import VideoJobManager


class FakeProvider:
    def generate(self, prompt, duration_seconds, aspect_ratio):
        return b"\x00\x00\x00\x18ftypmp42fake-video"


class FailingProvider:
    def generate(self, prompt, duration_seconds, aspect_ratio):
        raise RuntimeError("simulated provider failure")


class VideoJobManagerTests(unittest.TestCase):
    def make_manager(self, root, provider):
        return VideoJobManager(
            database=Path(root) / "jobs.sqlite3",
            output_dir=Path(root) / "videos",
            provider_factory=provider,
        )

    def wait_for(self, manager, job_id):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            job = manager.get(job_id)
            if job["status"] in {"completed", "failed"}:
                return job
            time.sleep(0.01)
        self.fail("job did not finish before timeout")

    def test_job_completes_and_video_is_persisted(self):
        with tempfile.TemporaryDirectory() as root:
            manager = self.make_manager(root, FakeProvider)
            try:
                job = manager.submit("A cinematic bus driving", 5, "16:9")
                result = self.wait_for(manager, job["id"])
                self.assertEqual(result["status"], "completed")
                self.assertTrue(manager.video_path(job["id"]).is_file())
            finally:
                manager.close()

    def test_provider_failure_is_recorded(self):
        with tempfile.TemporaryDirectory() as root:
            manager = self.make_manager(root, FailingProvider)
            try:
                job = manager.submit("A cinematic bus driving")
                result = self.wait_for(manager, job["id"])
                self.assertEqual(result["status"], "failed")
                self.assertIn("simulated provider failure", result["error"])
            finally:
                manager.close()

    def test_rejects_invalid_job_inputs(self):
        with tempfile.TemporaryDirectory() as root:
            manager = self.make_manager(root, FakeProvider)
            try:
                with self.assertRaises(ValueError):
                    manager.submit(" ")
                with self.assertRaises(ValueError):
                    manager.submit("prompt", 7)
                with self.assertRaises(ValueError):
                    manager.get("../secret")
            finally:
                manager.close()


if __name__ == "__main__":
    unittest.main()

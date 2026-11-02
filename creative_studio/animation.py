"""Timeline and image-animation helpers for short motion-graphics clips."""

from dataclasses import dataclass
from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from creative_studio.video import write_video


@dataclass(frozen=True)
class Timeline:
    """A fixed-rate animation timeline."""

    fps: int = 30
    duration_seconds: float = 6.0

    def __post_init__(self) -> None:
        if self.fps <= 0:
            raise ValueError("fps must be greater than zero")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than zero")

    @property
    def frame_count(self) -> int:
        return max(1, round(self.fps * self.duration_seconds))

    def time_at(self, frame_index: int) -> float:
        if not 0 <= frame_index < self.frame_count:
            raise IndexError("frame_index is outside this timeline")
        return frame_index / self.fps


def ease(progress: float, mode: str = "ease-in-out") -> float:
    """Map progress in [0, 1] through a named easing curve."""
    if not 0.0 <= progress <= 1.0:
        raise ValueError("progress must be between 0 and 1")
    if mode == "linear":
        return progress
    if mode == "ease-in":
        return progress * progress
    if mode == "ease-out":
        return 1.0 - (1.0 - progress) ** 2
    if mode == "ease-in-out":
        return 3 * progress**2 - 2 * progress**3
    raise ValueError("mode must be linear, ease-in, ease-out, or ease-in-out")


def render_ken_burns(source: str | Path, output: str | Path,
                     duration: float = 5.0, fps: int = 24,
                     start_zoom: float = 1.0, end_zoom: float = 1.2,
                     start_focus: tuple[float, float] = (0.5, 0.5),
                     end_focus: tuple[float, float] = (0.5, 0.5),
                     easing: str = "ease-in-out") -> Path:
    """Render a smooth pan/zoom (Ken Burns) MP4 from one still image.

    Focus coordinates are normalized image positions: (0, 0) is top-left
    and (1, 1) is bottom-right. The source image is never modified.
    """
    timeline = Timeline(fps=fps, duration_seconds=duration)
    if start_zoom < 1.0 or end_zoom < 1.0:
        raise ValueError("zoom values must be at least 1.0")
    for focus in (start_focus, end_focus):
        if len(focus) != 2 or any(not 0.0 <= value <= 1.0 for value in focus):
            raise ValueError("focus coordinates must be pairs between 0 and 1")
    ease(0.5, easing)  # Validate the selected easing mode before opening output.

    with Image.open(source) as opened:
        image = opened.convert("RGB")
    width, height = image.size
    if width < 2 or height < 2:
        raise ValueError("source image must be at least 2 by 2 pixels")

    def frames() -> Iterator[np.ndarray]:
        for index in range(timeline.frame_count):
            raw = 0.0 if timeline.frame_count == 1 else index / (timeline.frame_count - 1)
            progress = ease(raw, easing)
            zoom = start_zoom + (end_zoom - start_zoom) * progress
            focus_x = start_focus[0] + (end_focus[0] - start_focus[0]) * progress
            focus_y = start_focus[1] + (end_focus[1] - start_focus[1]) * progress
            crop_width = max(1, round(width / zoom))
            crop_height = max(1, round(height / zoom))
            center_x, center_y = focus_x * width, focus_y * height
            left = min(max(0, round(center_x - crop_width / 2)), width - crop_width)
            top = min(max(0, round(center_y - crop_height / 2)), height - crop_height)
            frame = image.crop((left, top, left + crop_width, top + crop_height))
            frame = frame.resize((width, height), Image.Resampling.LANCZOS)
            yield cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2BGR)

    return write_video(frames(), output, fps=fps)

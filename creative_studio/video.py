"""OpenCV video utilities with explicit validation."""

from pathlib import Path
from collections.abc import Iterable
import cv2
import numpy as np


def write_video(frames: Iterable[np.ndarray], output: str | Path,
                fps: int = 30) -> Path:
    """Write BGR uint8 frames to an MP4 file and return its path."""
    if fps <= 0:
        raise ValueError("fps must be greater than zero")

    iterator = iter(frames)
    try:
        first = next(iterator)
    except StopIteration as exc:
        raise ValueError("at least one frame is required") from exc

    _validate_frame(first)
    height, width = first.shape[:2]
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"),
                             fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError("Could not open video writer; check codec support")

    try:
        writer.write(first)
        for frame in iterator:
            _validate_frame(frame)
            if frame.shape[:2] != (height, width):
                raise ValueError("all frames must have the same dimensions")
            writer.write(frame)
    finally:
        writer.release()

    return output_path


def _validate_frame(frame: np.ndarray) -> None:
    if not isinstance(frame, np.ndarray):
        raise TypeError("each frame must be a NumPy array")
    if frame.dtype != np.uint8 or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("each frame must be a uint8 BGR image with 3 channels")

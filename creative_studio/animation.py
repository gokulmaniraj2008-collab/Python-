"""Small, dependency-free animation timing helpers."""

from dataclasses import dataclass


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
        return round(self.fps * self.duration_seconds)

    def time_at(self, frame_index: int) -> float:
        if not 0 <= frame_index < self.frame_count:
            raise IndexError("frame_index is outside this timeline")
        return frame_index / self.fps

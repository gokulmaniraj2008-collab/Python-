"""Image helpers built on Pillow."""

from pathlib import Path
from PIL import Image


def create_thumbnail(source: str | Path, destination: str | Path,
                     size: tuple[int, int] = (512, 512)) -> Path:
    """Create a proportional thumbnail and save it to destination."""
    if len(size) != 2 or any(dimension <= 0 for dimension in size):
        raise ValueError("size must contain two positive dimensions")

    source_path = Path(source)
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as image:
        image.thumbnail(size)
        image.save(destination_path)

    return destination_path

"""Command-line entry point for Python Creative AI Studio."""

import argparse
import os
from pathlib import Path

from creative_studio import __version__
from creative_studio.animation import render_ken_burns
from creative_studio.generation import generate_image
from creative_studio.providers.huggingface import HuggingFaceImageProvider
from creative_studio.video import create_video_from_images


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="creative-studio",
        description="Python-first utilities for creative image, video, and animation work.",
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("info", help="show studio information")

    image_parser = commands.add_parser("generate-image", help="generate an image using Hugging Face")
    image_parser.add_argument("--prompt", required=True, help="describe the image to create")
    image_parser.add_argument("--output", default="outputs/generated-image.png")
    image_parser.add_argument("--model", default=os.getenv(
        "HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell"
    ))

    video_parser = commands.add_parser("images-to-video", help="assemble images into an MP4")
    video_parser.add_argument("--input-dir", required=True, help="directory of ordered image frames")
    video_parser.add_argument("--output", default="outputs/generated-video.mp4")
    video_parser.add_argument("--fps", type=int, default=24)

    animation_parser = commands.add_parser("animate-image", help="create a cinematic pan/zoom MP4 from one image")
    animation_parser.add_argument("--input", required=True, help="source image path")
    animation_parser.add_argument("--output", default="outputs/animated-scene.mp4")
    animation_parser.add_argument("--duration", type=float, default=5.0)
    animation_parser.add_argument("--fps", type=int, default=24)
    animation_parser.add_argument("--start-zoom", type=float, default=1.0)
    animation_parser.add_argument("--end-zoom", type=float, default=1.2)
    animation_parser.add_argument("--easing", choices=("linear", "ease-in", "ease-out", "ease-in-out"), default="ease-in-out")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in (None, "info"):
        print(f"Python Creative AI Studio {__version__}")
        print("Modules: image, video, animation, generation, providers")
        print("Legacy generator: python create_stick_hero.py")
        return 0

    if args.command == "generate-image":
        provider = HuggingFaceImageProvider(model=args.model)
        result = generate_image(provider, args.prompt, args.output)
        print(f"Image saved: {result}")
        return 0

    if args.command == "images-to-video":
        folder = Path(args.input_dir)
        if not folder.is_dir():
            raise SystemExit(f"Input directory does not exist: {folder}")
        image_paths = sorted(
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
        result = create_video_from_images(image_paths, args.output, fps=args.fps)
        print(f"Video saved: {result}")
        return 0

    if args.command == "animate-image":
        result = render_ken_burns(
            args.input, args.output, duration=args.duration, fps=args.fps,
            start_zoom=args.start_zoom, end_zoom=args.end_zoom, easing=args.easing,
        )
        print(f"Animation saved: {result}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

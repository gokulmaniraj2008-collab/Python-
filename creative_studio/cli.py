"""Command-line entry point for Python Creative AI Studio."""

import argparse

from creative_studio import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="creative-studio",
        description="Python-first utilities for creative image, video, and animation work.",
    )
    parser.add_argument("command", nargs="?", choices=("info",), default="info")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "info":
        print(f"Python Creative AI Studio {__version__}")
        print("Modules: image, video, animation")
        print("Legacy generator: python create_stick_hero.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

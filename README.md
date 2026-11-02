# Python Creative AI Studio

A modular Python-first toolkit for image processing, video generation, and animation experiments. The existing Stick Hero Studio browser app and create_stick_hero.py generator remain supported.

## Quick start

Python 3.10+ recommended.

    python -m venv .venv
    python -m pip install -r requirements.txt
    python -m unittest discover -s tests -v
    python create_stick_hero.py

Open index.html in a modern browser for the existing web animation studio. The legacy generator writes stick_figure_hero.mp4 in the repository root.

## Architecture

    creative_studio/
      __init__.py
      __main__.py
      cli.py
      animation.py
      image.py
      video.py
    tests/
      test_animation.py
      test_image.py
      test_video.py
    .github/workflows/python-ci.yml

## Dependencies

numpy and opencv-python-headless provide numerical/video processing; Pillow provides image utilities. Optional AI/ML packages are listed separately in requirements-ai.txt and are not installed by default.

PyTorch, ComfyUI, and Blender require separate runtime and hardware decisions, so they are reserved for later phases. Vercel continues to serve the static website; Python generation and tests run locally or in GitHub Actions. Vercel static hosting is not a persistent Python backend.

This phase only adds files. Existing index.html and create_stick_hero.py are intentionally unchanged.

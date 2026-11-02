# Python Creative AI Studio

A modular Python-first toolkit for image generation, image processing, video creation, and animation experiments. The existing Stick Hero Studio browser app and `create_stick_hero.py` generator remain supported.

## Quick start

Python 3.10+ recommended.

    python -m venv .venv
    python -m pip install -r requirements.txt
    python -m unittest discover -s tests -v
    python -m creative_studio info

Open `index.html` in a modern browser for the existing web animation studio. The legacy generator writes `stick_figure_hero.mp4` in the repository root.

## Generate an AI image (optional remote provider)

The Hugging Face adapter uses the Inference Providers router. Create a Hugging Face access token with permission to call inference providers, then set it as an environment variable named `HF_TOKEN`. Never commit the token or put it in browser JavaScript.

    export HF_TOKEN="your-token"
    python -m creative_studio generate-image --prompt "A cinematic tiny robot in a rainy neon city" --output outputs/robot.png

You can select another compatible image model with `--model` or the `HF_IMAGE_MODEL` environment variable. The default is `black-forest-labs/FLUX.1-schnell`. Model access, provider availability, usage quotas, and pricing can change; this is not guaranteed to be free.

## Create a video from images

Put image frames in one folder using sortable names such as `001.png`, `002.png`, and `003.png`. All images must have identical dimensions.

    python -m creative_studio images-to-video --input-dir frames --output outputs/scene.mp4 --fps 24

This assembles an ordered image sequence into MP4. It does not generate new video content with a diffusion model.

## Animate a still image (Phase 3)

Create a cinematic pan-and-zoom (Ken Burns) animation from a single image. Choose a zoom range, duration, frame rate, and easing curve:

    python -m creative_studio animate-image --input photo.png --output outputs/cinematic.mp4 --duration 5 --fps 24 --start-zoom 1.0 --end-zoom 1.25 --easing ease-in-out

Supported easing curves: `linear`, `ease-in`, `ease-out`, and `ease-in-out`. This is deterministic Python animation—not text-to-video AI. It runs with the existing Pillow, NumPy, and OpenCV dependencies and does not download a model.

## Architecture

    creative_studio/
      providers/          # provider protocol and Hugging Face adapter
      generation.py       # provider-independent image generation
      image.py            # Pillow image utilities
      video.py            # OpenCV MP4 and image-sequence assembly
      animation.py        # timeline, easing, and pan/zoom renderer
      cli.py              # command-line interface
    tests/                # offline unit tests

## Runtime notes

No heavyweight model is downloaded during installation or CI. Hugging Face image generation needs a user-provided token; model access, quotas, and pricing are controlled by the provider and are not guaranteed to be free. Vercel continues to serve the static website; Python generation and tests run locally or in GitHub Actions. Never expose `HF_TOKEN` in browser code.

Phase 3 adds the animation engine and CLI without changing the existing `index.html` Stick Hero website or `create_stick_hero.py` generator.

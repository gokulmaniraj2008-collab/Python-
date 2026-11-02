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

    # Linux/macOS shell example
    export HF_TOKEN="your-token"
    python -m creative_studio generate-image --prompt "A cinematic tiny robot in a rainy neon city" --output outputs/robot.png

You can select another compatible image model with `--model` or the `HF_IMAGE_MODEL` environment variable. The default is `black-forest-labs/FLUX.1-schnell`. Model access, provider availability, usage quotas, and pricing can change; this is not guaranteed to be free. The image command requires an internet connection and a valid token.

## Create a video from images

Put image frames in one folder using sortable names such as `001.png`, `002.png`, and `003.png`. All images must have identical dimensions.

    python -m creative_studio images-to-video --input-dir frames --output outputs/scene.mp4 --fps 24

This assembles the frames into an MP4 with OpenCV. It is an image-to-video assembly workflow, not a text-to-video diffusion model. A future phase can add dedicated video-generation providers.

## Architecture

    creative_studio/
      providers/          # provider protocol and Hugging Face adapter
      generation.py       # provider-independent generation workflow
      image.py            # Pillow image utilities
      video.py            # OpenCV MP4 and image-sequence assembly
      animation.py        # timeline utilities
      cli.py              # command-line interface
    tests/                # offline unit tests

## Dependencies and runtime notes

NumPy, OpenCV, and Pillow are the lightweight core. No heavyweight model is downloaded during installation or CI. The Hugging Face adapter uses Python's standard library for HTTP requests. PyTorch, ComfyUI, and Blender remain optional separate runtimes for later phases.

Vercel continues to serve the static website; Python generation and tests run locally or in GitHub Actions. Vercel static hosting is not a persistent Python backend. Never expose `HF_TOKEN` in a static website or client-side code.

The Phase 2 changes add modular generation support without changing the existing `index.html` Stick Hero website or `create_stick_hero.py` generator.

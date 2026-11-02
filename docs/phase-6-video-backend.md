# Phase 6 — Real text-to-video backend

Phase 6 adds an authenticated Python HTTP service, a background job worker, SQLite job history, MP4 delivery, and a browser integration in `studio.html`.

## Provider and free-tier reality

The default adapter uses Hugging Face Inference Providers with:

- Model: `Wan-AI/Wan2.2-TI2V-5B`
- Routed provider: `fal-ai`
- Server-side token: `HF_TOKEN`

Hugging Face documents a monthly $0.10 inference credit for free accounts. This is a small trial allowance, not a promise that a video request will be free or complete within the allowance. The application does not configure a payment method or enable a paid fallback. Check your account's credit and provider availability before submitting jobs. Model access, generation duration, dimensions, latency, and pricing are controlled by Hugging Face and the routed provider.

## Install and run the backend

Install the existing base dependencies plus the optional video dependency:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-video.txt
```

Create a Hugging Face token with Inference Providers permission. Set these server-side environment variables:

- `HF_TOKEN`: Hugging Face token (never expose it to the browser).
- `VIDEO_API_ACCESS_KEY`: a separate random API access secret, at least 24 characters.
- `VIDEO_CORS_ORIGINS`: comma-separated exact website origins, e.g. `https://python-chi-black.vercel.app`.
- `VIDEO_API_HOST`: defaults to `127.0.0.1`; set `0.0.0.0` only behind a trusted HTTPS host/proxy.
- Optional: `HF_VIDEO_MODEL`, `HF_VIDEO_PROVIDER`, `VIDEO_API_PORT`, `VIDEO_JOBS_DB`, `VIDEO_OUTPUT_DIR`.

Start the API:

```bash
python -m creative_studio.api
```

The API is a separate Python service; it is not executed by the static Vercel website. Deploy this worker on a Python host that supports long-running background work and persistent disk, terminate TLS at the host/proxy, then enter its HTTPS base URL and the separate `VIDEO_API_ACCESS_KEY` in the Studio page. The browser holds that access key only in memory for the current page session. The Hugging Face token remains exclusively on the backend.

## API

- `GET /health`: basic health check.
- `POST /jobs`: submit `{prompt, duration_seconds, aspect_ratio}`; returns HTTP 202 and a job id.
- `GET /jobs/{id}`: read status and, when complete, a video URL.
- `GET /jobs/{id}/video`: authenticated MP4 stream.

Every job endpoint requires `Authorization: Bearer <VIDEO_API_ACCESS_KEY>`. Prompts are limited to 2,000 characters; supported duration choices are 5, 8, 10, and 15 seconds; aspect-ratio selection is retained as metadata because final dimensions are model/provider-defined. Job metadata is stored in SQLite and MP4 files are stored under `outputs/videos/`. Jobs interrupted by a backend restart are marked failed rather than silently left processing.

## Website integration

The existing Vercel page now has a connected-backend panel in the text-to-video section. Set the backend HTTPS URL and API access key, then submit and poll jobs. Completed MP4 files are fetched with an authenticated request and previewed in the page. The key is not saved in local storage and is never sent to Vercel as a deployment secret. Existing command generation, image, animation, Stick Hero, and local gallery workflows remain available.

## Operational notes

This API service is intended to run behind HTTPS on a persistent Python host. The static Vercel frontend alone cannot run Python workers or persist SQLite data. The job database and MP4 output directory must live on persistent storage. Do not expose the service directly over plain HTTP to the public internet. Add a stronger per-user identity/rate limit before opening a shared public endpoint.

# Phase 5 — Text-to-video provider integration

## What this adds

- A provider-neutral asynchronous video-job adapter using Python's standard library.
- A REST contract: submit a job with `POST /jobs`, poll `GET /jobs/{id}`, and receive a completed HTTPS `video_url`.
- `generate-video` CLI command that submits, polls, records non-secret job metadata, and downloads the MP4.
- Job records under `outputs/video-jobs/` and a local browser video preview gallery in `studio.html`.
- No new mandatory packages or model downloads.

## Configure a compatible provider

Set these variables in the Python runtime (never in browser JavaScript):

- `VIDEO_API_URL`: HTTPS base URL for a provider implementing the contract below.
- `VIDEO_API_KEY`: private API key.

Submit request JSON:

```json
{"prompt":"A cinematic shot of a bus driving through a green village road","duration_seconds":5,"aspect_ratio":"16:9"}
```

Expected submit response:

```json
{"id":"job-123","status":"queued"}
```

Poll response:

```json
{"id":"job-123","status":"completed","video_url":"https://cdn.example/video.mp4"}
```

Supported statuses: `queued`, `processing`, `completed`, `failed`. A failed response may include an `error` string. The adapter never forwards the API key to the returned video CDN URL.

## Run

```bash
python -m creative_studio generate-video --prompt "A cinematic village road scene" --duration 5 --aspect-ratio 16:9 --output outputs/scene.mp4
```

## Important limits

This is a generic adapter, not a claim that a particular video provider is configured or free. A provider must implement the REST contract above and may charge for generation. The repository does not contain a provider key. The static Vercel page does not execute Python; the command runs in a Python environment. Job JSON is local runtime metadata, not a shared cloud database. The browser gallery previews files selected on the current device only.

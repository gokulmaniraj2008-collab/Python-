# Python Creative AI Studio — Web workspace

Phase 4 adds a separate mobile-friendly static frontend at `/studio.html`. The existing `index.html` Stick Hero experience remains unchanged.

## Open the web workspace

After the branch is merged and Vercel deploys the production branch, open:

    https://YOUR-VERCEL-DOMAIN/studio.html

The page supports local image preview, prompt entry, model selection, animation settings, and copyable Python CLI commands. It does not execute Python in the browser.

## Runtime boundary

Vercel static hosting serves HTML, CSS, and JavaScript. Python generation runs in a Python environment (local machine, GitHub Actions, or a separately deployed backend). The static page never receives or stores `HF_TOKEN`, and selected images are previewed locally in the browser rather than uploaded to a provider.

## Commands prepared by the page

- `python -m creative_studio generate-image ...`
- `python -m creative_studio animate-image ...`

Install the project dependencies first with `pip install -r requirements.txt`.

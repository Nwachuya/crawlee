# crawl

Ultra-light FastAPI service for three web-content workflows:

- scrape a page into markdown, links, images, and optional chunks
- audit a page for hidden prompt-injection and secret-leak patterns
- generate synthetic Q&A dataset pairs from documentation-style pages

The app is intentionally small: one FastAPI entrypoint in [main.py](/Users/o.nwachuya/Claude/Projects/HQ/Crawlee/main.py), a Docker image, and a focused regression suite.

## Endpoints

### `GET /health`

Simple liveness endpoint:

```json
{"status":"ok"}
```

### `POST /scrape`

Fetches a target URL, extracts markdown with `trafilatura`, collects images and links, and can optionally chunk the markdown output.

Request body:

```json
{
  "url": "https://stripe.com/docs",
  "impersonate": "chrome120",
  "chunk_size": 0,
  "chunk_overlap": 100,
  "selectors": {
    "headings": "h1, h2"
  },
  "fit_markdown": false,
  "sanitize_injections": true
}
```

Notes:

- `chunk_size` must be `0` or greater
- if `chunk_size > 0`, then `chunk_overlap` must be smaller than `chunk_size`
- invalid URLs and invalid chunk settings return `422`
- upstream fetch failures preserve the upstream HTTP status when possible

### `POST /security-audit`

Fetches a page and scans it for:

- hidden prompt-injection content in common CSS-hiding patterns
- offscreen hidden content like `left: -9999px`
- HTML comment injections
- hostile instructions carried in attributes and meta tags
- script-embedded secret patterns
- Unicode homoglyph and zero-width obfuscation

Request body:

```json
{
  "url": "https://sluxia.com/ohu/security-test.html",
  "impersonate": "chrome120"
}
```

Example classes of findings:

- `hidden_css_element`
- `comment_injection`
- `attribute_injection`
- `secret_pattern`
- `prompt_injection_pattern`
- `zero_width_characters`

### `POST /dataset`

Fetches a page and tries to turn documentation-style content into synthetic Q&A pairs with export-ready formats.

Request body:

```json
{
  "url": "https://developers.cloudflare.com/fundamentals/",
  "impersonate": "chrome120",
  "min_confidence": 0.8
}
```

Response includes:

- `dataset_health`
- `exports.openai_chatml`
- `exports.dpo_preference`
- `dataset` array with questions, answers, taxonomy, and token estimates

The generator first uses DOM headings, then falls back to markdown section extraction, and finally paragraph-based sections for prose-heavy docs pages.

## Local Development

### Requirements

- Python 3.12 is the tested local runtime
- Docker is optional for container testing

Python 3.14 was not a good fit during local verification because `selectolax==0.3.21` failed to build there. The included Docker image uses Python 3.11.

### Setup

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt pytest
```

### Run locally

```bash
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

### Run tests

```bash
.venv/bin/python -m pytest -q
```

As of August 29, 2026, the local regression suite passes with 14 tests.

## Docker

Build:

```bash
docker build -t crawl .
```

Run:

```bash
docker run --rm -p 8000:8000 crawl
```

The image includes a container healthcheck against `/health`:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl --fail http://127.0.0.1:8000/health || exit 1
```

## Example Requests

### Health

```bash
curl http://127.0.0.1:8000/health
```

### Scrape

```bash
curl -X POST http://127.0.0.1:8000/scrape \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://stripe.com/docs"}'
```

### Security audit

```bash
curl -X POST http://127.0.0.1:8000/security-audit \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://sluxia.com/ohu/security-test.html"}'
```

### Dataset generation

```bash
curl -X POST http://127.0.0.1:8000/dataset \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://developers.cloudflare.com/fundamentals/"}'
```

## Deployment Notes

If a Docker-based deployment reports:

```text
failed to read dockerfile: open Dockerfile: no such file or directory
```

the repo likely imported correctly, but the deployment platform is using the wrong build context or Dockerfile path.

For Coolify-style Dockerfile deploys, verify:

- build pack is set to `Dockerfile`
- base directory is the repo root
- Dockerfile path is exactly `Dockerfile`
- exposed application port is `8000`

## Project Layout

```text
.
├── Dockerfile
├── README.md
├── main.py
├── requirements.txt
└── tests/
```

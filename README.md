# crawlee

FastAPI service for three web-content workflows:

- scrape a page into markdown, links, images, and optional chunks
- audit a page for hidden prompt-injection and secret-leak patterns
- generate synthetic Q&A dataset pairs from documentation-style pages

The service now includes a first-class site detection layer inside `/scrape` so extraction can adapt to common site infrastructures before falling back to low-content verdicts.

Dependencies use progressive top-level ranges in [requirements.in](/Users/o.nwachuya/Claude/Projects/HQ/Crawlee/requirements.in) and [requirements-dev.in](/Users/o.nwachuya/Claude/Projects/HQ/Crawlee/requirements-dev.in), with compiled lockfiles in [requirements.txt](/Users/o.nwachuya/Claude/Projects/HQ/Crawlee/requirements.txt) and `requirements-dev.txt`.

## Endpoints

### `GET /health`

Simple liveness endpoint:

```json
{"status":"ok"}
```

### `POST /scrape`

Fetches a target URL, detects the site type, chooses an extraction strategy, and returns markdown, links, images, optional chunks, plus diagnostics.

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
- detection always runs and uses only the current stack: `curl_cffi`, `trafilatura`, `selectolax`, `fastapi`, `pydantic`, and the standard library

Response includes these scrape-specific additions:

- `site_detection`
- `extraction_diagnostics`

Example shape:

```json
{
  "success": true,
  "url": "https://nextjs.org/docs",
  "content": {
    "markdown": "# Docs",
    "chunks": []
  },
  "links": {
    "internal": [],
    "external": []
  },
  "site_detection": {
    "platform_origin": "nextjs",
    "runtime_family": "react_meta_framework",
    "framework": "nextjs",
    "render_mode": "ssr_or_static",
    "confidence": 0.9,
    "matched_detectors": ["nextjs_site"],
    "signals": ["__NEXT_DATA__ marker", "_next asset path"],
    "recommended_strategy": "docs_content",
    "secondary_matches": []
  },
  "extraction_diagnostics": {
    "attempted_strategies": ["default_extract", "docs_main_extract"],
    "final_strategy": "docs_main_extract",
    "content_quality": "good",
    "visible_text_chars": 4820,
    "markdown_chars": 4820,
    "headings_found": 14,
    "internal_links_found": 63,
    "fallback_used": true,
    "failure_reason": null
  }
}
```

#### Detector catalog

The `/scrape` detector registry ships with 15 primary platform/framework detectors:

- `wordpress_core`
- `shopify_storefront`
- `webflow_site`
- `framer_site`
- `wix_site`
- `squarespace_site`
- `nextjs_site`
- `nuxt_site`
- `astro_site`
- `angular_app`
- `docusaurus_docs`
- `vitepress_docs`
- `mkdocs_material`
- `lovable_built`
- `bolt_built`

If no detector clears the confidence threshold, the response falls back to:

- `platform_origin=unknown`
- `runtime_family=unknown`
- `recommended_strategy=generic_html`

#### Strategy families

Detector results map into these extraction strategy families:

- `generic_html`
- `static_marketing`
- `cms_content`
- `docs_content`
- `commerce_content`
- `spa_shell`
- `ai_builder_marketing`

The fallback chain is deterministic and ends with a low-content verdict instead of falsely reporting a thin shell page as a successful extract.

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

## Local Development

### Requirements

- Python 3.12 is the tested local runtime
- Docker is optional for container testing

Python 3.14 was not a good fit during local verification because `selectolax==0.3.21` failed to build there. The included Docker image uses Python 3.11.

### Setup

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

### Run locally

```bash
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

### Run tests

```bash
.venv/bin/python -m pytest -q
```

### Refresh lockfiles

```bash
.venv/bin/pip-compile --strip-extras requirements.in
.venv/bin/pip-compile --strip-extras requirements-dev.in
```

As of August 30, 2026, the local regression suite passes with 36 tests.

## Docker

Build:

```bash
docker build -t crawlee .
```

Run:

```bash
docker run --rm -p 8000:8000 crawlee
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

## Project Layout

```text
.
├── Dockerfile
├── README.md
├── app
│   ├── application.py
│   ├── routes
│   ├── schemas.py
│   └── services
│       ├── dataset.py
│       ├── detection.py
│       ├── fetch.py
│       ├── scrape.py
│       ├── security.py
│       └── strategy.py
├── main.py
└── requirements.txt
```

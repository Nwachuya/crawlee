# Crawlee Memory

## Contacts

| Name | Role | Context |
|---|---|---|
| Obi Nwachuya | Owner & System Architect | Creator of the Crawlee web extraction engine. |

## Key Decisions & Architecture

- **Engine Architecture:** High-speed, standalone FastAPI scraping and intelligence service.
- **Python Runtime:** Python 3.12 (`selectolax==0.3.21` requires Python 3.12/3.11; Python 3.14 build is incompatible).
- **Live Deployment:** Coolify at `https://crawlee.sluxia.com`. All endpoints under `/api/v1` prefix.
- **Auth:** `X-Api-Key` header required on all endpoints except `/api/v1/health`. Key stored as `X_API_KEY` env var in Coolify and locally in `.env` (gitignored).
- **Core Endpoints:**
  - `GET /api/v1/health` — Liveness health check (open, no key required).
  - `POST /api/v1/scrape` — Platform detection, adaptive extraction (markdown, chunks, links, images).
  - `POST /api/v1/security-audit` — Hidden CSS, comment injection, zero-width obfuscation, secret patterns.
  - `POST /api/v1/dataset` — Synthetic Q&A dataset generation (OpenAI ChatML & DPO formats).
- **Detector Catalog (16 entries; 15 platform detectors + PHP auxiliary):** WordPress, Shopify, Webflow, Framer, Wix, Squarespace, Next.js, Nuxt, Astro, Angular, Docusaurus, VitePress, MkDocs Material, Lovable, Bolt, php_server_rendered.
- **Strategy Families:** `generic_html`, `static_marketing`, `cms_content`, `docs_content`, `commerce_content`, `spa_shell`, `ai_builder_marketing`.
- **Docker Deployment:** Python 3.11 base image with container healthcheck on `/api/v1/health`.

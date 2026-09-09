# Crawlee Memory

## Contacts

| Name | Role | Context |
|---|---|---|
| Obi Nwachuya | Owner & System Architect | Creator of the Crawlee web extraction engine. |

## Key Decisions & Architecture

- **Engine Architecture:** High-speed, standalone FastAPI scraping and intelligence service.
- **Python Runtime:** Python 3.12 (`selectolax==0.3.21` requires Python 3.12/3.11; Python 3.14 build is incompatible).
- **Core Endpoints:**
  - `GET /health` — Liveness health check.
  - `POST /scrape` — Platform detection, adaptive extraction (markdown, chunks, links, images).
  - `POST /security-audit` — Hidden CSS, comment injection, zero-width obfuscation, secret patterns.
  - `POST /dataset` — Synthetic Q&A dataset generation (OpenAI ChatML & DPO formats).
- **Detector Catalog (15 Platforms):** WordPress, Shopify, Webflow, Framer, Wix, Squarespace, Next.js, Nuxt, Astro, Angular, Docusaurus, VitePress, MkDocs Material, Lovable, Bolt.
- **Strategy Families:** `generic_html`, `static_marketing`, `cms_content`, `docs_content`, `commerce_content`, `spa_shell`, `ai_builder_marketing`.
- **Docker Deployment:** Python 3.11 base image with container healthcheck on `/health`.

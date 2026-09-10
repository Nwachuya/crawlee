# CLAUDE.md — Crawlee Workstation

## Identity

Crawlee is a high-performance FastAPI service providing three core web intelligence workflows:
1. **Adaptive Web Scraping (`/api/v1/scrape`):** Automated site framework detection (16 registry entries — 15 threshold-clearing platform detectors plus a weak PHP fallback signal: Next.js, Shopify, Webflow, Framer, Wix, Docusaurus, VitePress, etc.) and adaptive extraction strategy execution (markdown, links, images, optional chunks).
2. **Security & Prompt Injection Audit (`/api/v1/security-audit`):** Hidden CSS elements, off-screen text, HTML comment injections, hostile attributes, script-embedded secrets, and zero-width obfuscation scanning.
3. **Synthetic Q&A Dataset Generation (`/api/v1/dataset`):** Ingestion of documentation-style pages into export-ready OpenAI ChatML and DPO preference datasets.

## Resources

| Resource | Read when... |
|---|---|
| [README.md](file:///Users/o.nwachuya/Claude/Projects/HQ/Crawlee/README.md) | Reviewing endpoint specifications, request/response JSON schemas, and local test instructions. |
| [requirements.in](file:///Users/o.nwachuya/Claude/Projects/HQ/Crawlee/requirements.in) | Inspecting core Python dependencies and lockfile compilation rules. |

## Workflow

1. **Local Setup:**
   - Python 3.12 runtime (`.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000`).
   - Copy `.env` and set `X_API_KEY` for local auth testing.
   - Run test suite: `.venv/bin/python -m pytest -q` (36 passing regression tests).
   - Refresh lockfiles with `pip-compile`:
     ```bash
     .venv/bin/pip-compile --strip-extras requirements.in
     .venv/bin/pip-compile --strip-extras requirements-dev.in
     ```
2. **Live Deployment:**
   - Deployed on Coolify at `https://crawlee.sluxia.com`.
   - All endpoints prefixed `/api/v1`. `/api/v1/health` is open; all others require `X-Api-Key` header.
   - `X_API_KEY` is set as a Coolify environment variable.
3. **Execution Rules:**
   - Detection uses `curl_cffi`, `trafilatura`, `selectolax`, `fastapi`, and `pydantic`.
   - Never fall back to low-content verdicts without attempting the matching platform strategy first.
   - Preserves upstream HTTP status codes when upstream fetches fail.

## Editorial Rules

Follow Obi's voice principles by loading the brainbox identity files (`Brainbox/identity/voice.md`, `banned.md`, `beliefs.md`, `writing_samples.md`) and running the final voice pass against `banned.md` + the anti-AI-slop lesson (`Brainbox/knowledge/lessons/lesson-2026-08-anti-ai-slop-tells`).

## Memory System

At the start of every session, read [MEMORY.md](file:///Users/o.nwachuya/Claude/Projects/HQ/Crawlee/MEMORY.md) before responding. Use what you find to inform your work. Do not announce what was read.

When Obi says "remember this," write the information to [MEMORY.md](file:///Users/o.nwachuya/Claude/Projects/HQ/Crawlee/MEMORY.md) immediately and confirm.

**Where things go:**
- **Test 1 (Rules/Behaviors):** Add to this file (`Crawlee/CLAUDE.md`).
- **Test 2 (Facts/Statuses/Detectors):** Add to [MEMORY.md](file:///Users/o.nwachuya/Claude/Projects/HQ/Crawlee/MEMORY.md).

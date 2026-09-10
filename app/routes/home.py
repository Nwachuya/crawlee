from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Crawlee — Web Intelligence API</title>
  <meta name="description" content="Crawlee is a FastAPI service for adaptive web scraping, prompt-injection security auditing, and synthetic Q&A dataset generation. 15 platform detectors. Zero-browser architecture." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/iconify-icon@1.0.8/dist/iconify-icon.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --color-background: #f6f6f4;
      --color-surface: #ffffff;
      --color-text: #141414;
      --color-text-muted: #8a8a86;
      --color-border: #e3e3de;
      --color-border-light: #eeeeea;
      --color-accent: #121212;
      --color-accent-hover: #000000;
      --color-accent-light: #eeeeea;
      --color-success: #41D333;
      --color-warning: #F8D311;
      --color-danger: #F73730;
      --radius: 0;
      --radius-pill: 9999px;
      --shadow-card: none;
    }

    html.dark {
      --color-background: #141414;
      --color-surface: #1e1e1e;
      --color-text: #f6f6f4;
      --color-text-muted: #9b9b96;
      --color-border: #2e2e2a;
      --color-border-light: #252522;
      --color-accent: #f6f6f4;
      --color-accent-hover: #ffffff;
      --color-accent-light: #252522;
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: 'Poppins', sans-serif;
      font-size: 15px;
      line-height: 1.5;
      letter-spacing: -0.012em;
      background-color: var(--color-background);
      color: var(--color-text);
      transition: background-color 0.3s ease, color 0.3s ease;
    }

    .grid-bg {
      background-image:
        linear-gradient(var(--color-border-light) 1px, transparent 1px),
        linear-gradient(90deg, var(--color-border-light) 1px, transparent 1px);
      background-size: 58px 58px;
    }

    h1, h2, h3, h4 {
      font-family: 'Manrope', sans-serif;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1.15;
    }

    /* TOPBAR */
    .topbar {
      position: sticky;
      top: 0;
      z-index: 100;
      height: 72px;
      background: rgba(255,255,255,0.85);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--color-border);
      display: flex;
      align-items: center;
      transition: background 0.3s ease, border-color 0.3s ease;
    }
    html.dark .topbar { background: rgba(20,20,20,0.85); }

    .topbar-inner {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 24px;
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
      color: var(--color-text);
    }

    .brand-mark {
      width: 32px;
      height: 32px;
      background: var(--color-accent);
      border-radius: var(--radius-pill);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.3s ease;
    }
    .brand-mark iconify-icon { color: var(--color-background); font-size: 16px; }

    .brand-name {
      font-family: 'Manrope', sans-serif;
      font-weight: 800;
      font-size: 17px;
      letter-spacing: -0.03em;
    }

    .topbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .topbar-nav {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .topbar-nav a {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      font-family: 'Poppins', sans-serif;
      font-size: 13px;
      font-weight: 500;
      color: var(--color-text-muted);
      text-decoration: none;
      border-radius: var(--radius-pill);
      transition: color 0.2s ease, background 0.2s ease;
      letter-spacing: -0.01em;
    }
    .topbar-nav a:hover,
    .topbar-nav a.active {
      color: var(--color-text);
      background: var(--color-accent-light);
    }

    .topbar-divider {
      width: 1px;
      height: 20px;
      background: var(--color-border);
    }

    .register-btn {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 8px 18px;
      background: var(--color-accent);
      color: var(--color-background);
      font-family: 'Poppins', sans-serif;
      font-size: 13px;
      font-weight: 600;
      border: none;
      border-radius: var(--radius-pill);
      cursor: pointer;
      text-decoration: none;
      letter-spacing: -0.01em;
      transition: background 0.2s ease, transform 0.2s ease;
      white-space: nowrap;
    }
    .register-btn:hover { background: var(--color-accent-hover); transform: translateY(-1px); }

    .theme-toggle {
      width: 36px;
      height: 36px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--color-border);
      background: var(--color-surface);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-text-muted);
      font-size: 16px;
      transition: all 0.3s ease;
    }
    .theme-toggle:hover { border-color: var(--color-accent); color: var(--color-text); }

    /* PAGE WRAPPER */
    .page { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

    /* HERO */
    .hero {
      padding: 96px 0 80px;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 32px;
    }

    .hero-label {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 5px 14px;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-pill);
      font-size: 12px;
      font-weight: 600;
      color: var(--color-text-muted);
      letter-spacing: 0.04em;
      text-transform: uppercase;
      background: var(--color-surface);
    }

    .hero h1 {
      font-size: clamp(40px, 6vw, 72px);
      max-width: 820px;
      color: var(--color-text);
    }

    .hero-sub {
      font-size: 18px;
      color: var(--color-text-muted);
      max-width: 600px;
      line-height: 1.6;
    }

    .hero-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .btn-primary {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
      background: var(--color-accent);
      color: var(--color-background);
      font-family: 'Poppins', sans-serif;
      font-size: 14px;
      font-weight: 600;
      border: none;
      border-radius: var(--radius);
      cursor: pointer;
      text-decoration: none;
      transition: background 0.3s ease, transform 0.2s ease;
      letter-spacing: -0.012em;
    }
    .btn-primary:hover { background: var(--color-accent-hover); transform: translateY(-1px); }

    .btn-secondary {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
      background: transparent;
      color: var(--color-text);
      font-family: 'Poppins', sans-serif;
      font-size: 14px;
      font-weight: 600;
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
      cursor: pointer;
      text-decoration: none;
      transition: all 0.3s ease;
      letter-spacing: -0.012em;
    }
    .btn-secondary:hover { border-color: var(--color-accent); background: var(--color-accent-light); }

    /* DIVIDER */
    .divider { border: none; border-top: 1px solid var(--color-border); margin: 0; }

    /* ENDPOINTS SECTION */
    .section { padding: 80px 0; }
    .section-label {
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--color-text-muted);
      margin-bottom: 16px;
    }
    .section h2 { font-size: clamp(28px, 4vw, 40px); margin-bottom: 48px; }

    .endpoint-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1px;
      border: 1px solid var(--color-border);
      background: var(--color-border);
    }

    .endpoint-card {
      background: var(--color-surface);
      padding: 36px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      transition: background 0.2s ease;
    }
    .endpoint-card:hover { background: var(--color-accent-light); }

    .endpoint-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
    }

    .endpoint-icon {
      width: 40px;
      height: 40px;
      border: 1px solid var(--color-border);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-text);
      font-size: 18px;
      flex-shrink: 0;
      transition: border-color 0.3s ease;
    }

    .method-badge {
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.05em;
      background: var(--color-accent-light);
      color: var(--color-text-muted);
    }

    .endpoint-card h3 {
      font-size: 18px;
      color: var(--color-text);
    }

    .endpoint-path {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      color: var(--color-text-muted);
      background: var(--color-background);
      padding: 6px 10px;
      border: 1px solid var(--color-border-light);
      letter-spacing: 0;
    }

    .endpoint-desc {
      font-size: 14px;
      color: var(--color-text-muted);
      line-height: 1.6;
    }

    .tag-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .tag {
      padding: 3px 10px;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-pill);
      font-size: 11px;
      font-weight: 500;
      color: var(--color-text-muted);
      background: var(--color-background);
    }

    /* STATS */
    .stats-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1px;
      border: 1px solid var(--color-border);
      background: var(--color-border);
      margin-bottom: 80px;
    }
    .stat-cell {
      background: var(--color-surface);
      padding: 32px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .stat-number {
      font-family: 'Manrope', sans-serif;
      font-size: 36px;
      font-weight: 800;
      letter-spacing: -0.04em;
      color: var(--color-text);
    }
    .stat-label {
      font-size: 13px;
      color: var(--color-text-muted);
    }

    /* CODE SECTION */
    .code-section { padding: 80px 0; }
    .code-section h2 { font-size: clamp(28px, 4vw, 40px); margin-bottom: 8px; }
    .code-section .section-sub {
      font-size: 15px;
      color: var(--color-text-muted);
      margin-bottom: 32px;
    }

    /* Endpoint selector */
    .endpoint-selector {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 24px;
    }
    .ep-btn {
      padding: 7px 16px;
      font-family: 'Poppins', sans-serif;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-pill);
      background: transparent;
      color: var(--color-text-muted);
      transition: all 0.2s ease;
    }
    .ep-btn.active {
      background: var(--color-accent);
      color: var(--color-background);
      border-color: var(--color-accent);
    }
    .ep-btn:hover:not(.active) { color: var(--color-text); border-color: var(--color-accent); }

    /* Language tabs + copy button */
    .lang-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border: 1px solid var(--color-border);
      border-bottom: none;
      background: var(--color-background);
    }
    .lang-tabs { display: flex; }
    .lang-tab {
      padding: 10px 20px;
      font-family: 'Poppins', sans-serif;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      border: none;
      border-right: 1px solid var(--color-border);
      background: transparent;
      color: var(--color-text-muted);
      transition: all 0.2s ease;
    }
    .lang-tab.active { background: var(--color-surface); color: var(--color-text); }
    .lang-tab:hover:not(.active) { color: var(--color-text); }

    .copy-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 16px;
      margin-right: 8px;
      font-family: 'Poppins', sans-serif;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-pill);
      background: transparent;
      color: var(--color-text-muted);
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .copy-btn:hover { color: var(--color-text); border-color: var(--color-accent); }
    .copy-btn.copied { color: var(--color-success); border-color: var(--color-success); }

    .code-panel {
      border: 1px solid var(--color-border);
      background: var(--color-surface);
      padding: 28px 32px;
      overflow-x: auto;
      display: none;
      min-height: 200px;
    }
    .code-panel.active { display: block; }
    .code-panel pre {
      font-family: 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.8;
      color: var(--color-text);
      white-space: pre;
      margin: 0;
    }
    .code-comment { color: var(--color-text-muted); font-style: italic; }
    .code-key { color: var(--color-text); font-weight: 600; }
    .code-string { color: var(--color-text-muted); }

    /* AUTH SECTION */
    .auth-section {
      padding: 80px 0;
      border-top: 1px solid var(--color-border);
    }

    .auth-box {
      border: 1px solid var(--color-border);
      background: var(--color-surface);
      padding: 48px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 48px;
      align-items: start;
    }

    .auth-box h2 { font-size: 32px; margin-bottom: 16px; }
    .auth-box p { font-size: 15px; color: var(--color-text-muted); line-height: 1.6; margin-bottom: 24px; }

    .auth-rule {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 16px 0;
      border-bottom: 1px solid var(--color-border-light);
      font-size: 14px;
      color: var(--color-text-muted);
    }
    .auth-rule:last-child { border-bottom: none; }
    .auth-rule iconify-icon { font-size: 16px; margin-top: 2px; flex-shrink: 0; }
    .auth-rule strong { color: var(--color-text); display: block; margin-bottom: 2px; }

    .auth-code {
      border: 1px solid var(--color-border);
      background: var(--color-background);
      padding: 24px;
    }
    .auth-code pre {
      font-family: 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.8;
      color: var(--color-text);
      white-space: pre-wrap;
      word-break: break-all;
    }

    /* FOOTER */
    footer {
      border-top: 1px solid var(--color-border);
      padding: 32px 0;
    }
    .footer-inner {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .footer-inner p { font-size: 13px; color: var(--color-text-muted); }

    /* RESPONSIVE */
    @media (max-width: 768px) {
      .hero { padding: 64px 0 48px; }
      .hero-actions { flex-direction: column; align-items: flex-start; }
      .auth-box { grid-template-columns: 1fr; gap: 32px; padding: 32px; }
      .endpoint-grid { grid-template-columns: 1fr; }
      .footer-inner { flex-direction: column; align-items: flex-start; }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { transition: none !important; animation: none !important; }
    }
  </style>
</head>
<body class="grid-bg">

  <!-- TOPBAR -->
  <header class="topbar">
    <div class="topbar-inner">
      <a href="/" class="brand" aria-label="Crawlee home">
        <div class="brand-mark">
          <iconify-icon icon="lucide:zap" aria-hidden="true"></iconify-icon>
        </div>
        <span class="brand-name">Crawlee</span>
      </a>
      <div class="topbar-right">
        <nav class="topbar-nav" aria-label="Page sections">
          <a href="#endpoints" id="nav-endpoints">Endpoints</a>
          <a href="#examples" id="nav-examples">Quick start</a>
          <a href="#auth" id="nav-auth">Auth</a>
        </nav>
        <div class="topbar-divider" aria-hidden="true"></div>
        <a href="https://sluxia.com/crawlee/register" target="_blank" rel="noopener noreferrer" class="register-btn" id="registerBtn">
          Get access
          <iconify-icon icon="lucide:arrow-up-right" aria-hidden="true"></iconify-icon>
        </a>
        <button id="themeToggle" class="theme-toggle" aria-label="Toggle dark mode">
          <iconify-icon id="themeIcon" icon="lucide:moon" aria-hidden="true"></iconify-icon>
        </button>
      </div>
    </div>
  </header>

  <main>
    <div class="page">

      <!-- HERO -->
      <section class="hero">
        <span class="hero-label">
          <iconify-icon icon="lucide:cpu" aria-hidden="true"></iconify-icon>
          Web Intelligence API
        </span>
        <h1>Extract, audit, and train from any page on the web.</h1>
        <p class="hero-sub">
          Crawlee fetches pages through a TLS-spoofing client, fingerprints the underlying platform, picks the right extraction strategy, and returns clean structured data. No browser. No headless overhead.
        </p>
        <div class="hero-actions">
          <a href="#endpoints" class="btn-primary" id="viewEndpointsBtn">
            View endpoints
            <iconify-icon icon="lucide:arrow-down" aria-hidden="true"></iconify-icon>
          </a>
          <a href="#auth" class="btn-secondary" id="viewAuthBtn">
            Authentication
            <iconify-icon icon="lucide:key" aria-hidden="true"></iconify-icon>
          </a>
        </div>
      </section>

    </div>

    <hr class="divider" />

    <!-- STATS -->
    <div class="page">
      <div class="stats-row" style="margin-top: 80px;" role="list" aria-label="Key metrics">
        <div class="stat-cell" role="listitem">
          <span class="stat-number">16</span>
          <span class="stat-label">Detector entries</span>
        </div>
        <div class="stat-cell" role="listitem">
          <span class="stat-number">7</span>
          <span class="stat-label">Extraction strategy families</span>
        </div>
        <div class="stat-cell" role="listitem">
          <span class="stat-number">3</span>
          <span class="stat-label">Core endpoints</span>
        </div>
        <div class="stat-cell" role="listitem">
          <span class="stat-number">36</span>
          <span class="stat-label">Regression tests</span>
        </div>
      </div>

      <!-- ENDPOINTS -->
      <section class="section" id="endpoints" aria-labelledby="endpointsHeading">
        <p class="section-label">Endpoints</p>
        <h2 id="endpointsHeading">Three workflows. One base URL.</h2>

        <div class="endpoint-grid" role="list">

          <div class="endpoint-card" role="listitem">
            <div class="endpoint-header">
              <div class="endpoint-icon" aria-hidden="true">
                <iconify-icon icon="lucide:scan-text"></iconify-icon>
              </div>
              <span class="method-badge">POST</span>
            </div>
            <h3>Adaptive Scrape</h3>
            <div class="endpoint-path">/api/v1/scrape</div>
            <p class="endpoint-desc">
              Detects the site platform, selects the matching extraction strategy, and returns markdown, internal and external links, images, and optional token-aware chunks. Falls back deterministically, never silently.
            </p>
            <div class="tag-list" aria-label="Supported platforms">
              <span class="tag">WordPress</span>
              <span class="tag">Shopify</span>
              <span class="tag">Next.js</span>
              <span class="tag">Webflow</span>
              <span class="tag">Docusaurus</span>
              <span class="tag">+10 more</span>
            </div>
          </div>

          <div class="endpoint-card" role="listitem">
            <div class="endpoint-header">
              <div class="endpoint-icon" aria-hidden="true">
                <iconify-icon icon="lucide:shield-check"></iconify-icon>
              </div>
              <span class="method-badge">POST</span>
            </div>
            <h3>Security Audit</h3>
            <div class="endpoint-path">/api/v1/security-audit</div>
            <p class="endpoint-desc">
              Reads raw HTML before any extractor cleans it. Checks for hidden CSS injections, off-screen text, HTML comment vectors, hostile attributes, script-embedded secrets, and zero-width obfuscation.
            </p>
            <div class="tag-list" aria-label="Threat categories">
              <span class="tag">Prompt injection</span>
              <span class="tag">Secret patterns</span>
              <span class="tag">Hidden elements</span>
              <span class="tag">Zero-width</span>
            </div>
          </div>

          <div class="endpoint-card" role="listitem">
            <div class="endpoint-header">
              <div class="endpoint-icon" aria-hidden="true">
                <iconify-icon icon="lucide:database"></iconify-icon>
              </div>
              <span class="method-badge">POST</span>
            </div>
            <h3>Dataset Generator</h3>
            <div class="endpoint-path">/api/v1/dataset</div>
            <p class="endpoint-desc">
              Parses documentation-style pages into synthetic Q&amp;A pairs. Exports in OpenAI ChatML, Alpaca, ShareGPT, and DPO preference formats. Includes quality scores and token estimates per pair.
            </p>
            <div class="tag-list" aria-label="Export formats">
              <span class="tag">OpenAI ChatML</span>
              <span class="tag">DPO</span>
              <span class="tag">Alpaca</span>
              <span class="tag">ShareGPT</span>
            </div>
          </div>

        </div>
      </section>

      <!-- CODE EXAMPLES -->
      <section class="code-section" id="examples" aria-labelledby="examplesHeading">
        <p class="section-label">Quick start</p>
        <h2 id="examplesHeading">Copy and run.</h2>
        <p class="section-sub">Pick an endpoint and language. Your API key goes in the <code>X-Api-Key</code> header.</p>

        <!-- Endpoint selector -->
        <div class="endpoint-selector" role="group" aria-label="Select endpoint">
          <button class="ep-btn active" id="ep-scrape" onclick="switchEndpoint('scrape')">Scrape</button>
          <button class="ep-btn" id="ep-audit" onclick="switchEndpoint('audit')">Security audit</button>
          <button class="ep-btn" id="ep-dataset" onclick="switchEndpoint('dataset')">Dataset</button>
        </div>

        <!-- Language tabs + copy -->
        <div class="lang-bar">
          <div class="lang-tabs" role="tablist" aria-label="Language">
            <button class="lang-tab active" id="lt-curl" role="tab" aria-selected="true" onclick="switchLang('curl')">curl</button>
            <button class="lang-tab" id="lt-js" role="tab" aria-selected="false" onclick="switchLang('js')">JavaScript</button>
            <button class="lang-tab" id="lt-py" role="tab" aria-selected="false" onclick="switchLang('py')">Python</button>
          </div>
          <button class="copy-btn" id="copyBtn" onclick="copyCode()" aria-label="Copy code to clipboard">
            <iconify-icon icon="lucide:copy" aria-hidden="true"></iconify-icon>
            Copy
          </button>
        </div>

        <!-- scrape / curl -->
        <div id="code-scrape-curl" class="code-panel active" role="tabpanel">
          <pre id="pre-scrape-curl">curl -X POST https://crawlee.sluxia.com/api/v1/scrape \&#10;  -H 'Content-Type: application/json' \&#10;  -H 'X-Api-Key: YOUR_KEY' \&#10;  -d '{&#10;    "url": "https://stripe.com/docs",&#10;    "fit_markdown": true,&#10;    "chunk_size": 500,&#10;    "chunk_overlap": 80&#10;  }'</pre>
        </div>
        <!-- scrape / js -->
        <div id="code-scrape-js" class="code-panel" role="tabpanel">
          <pre id="pre-scrape-js">const res = await fetch('https://crawlee.sluxia.com/api/v1/scrape', {&#10;  method: 'POST',&#10;  headers: {&#10;    'Content-Type': 'application/json',&#10;    'X-Api-Key': 'YOUR_KEY'&#10;  },&#10;  body: JSON.stringify({&#10;    url: 'https://stripe.com/docs',&#10;    fit_markdown: true,&#10;    chunk_size: 500,&#10;    chunk_overlap: 80&#10;  })&#10;});&#10;const data = await res.json();</pre>
        </div>
        <!-- scrape / python -->
        <div id="code-scrape-py" class="code-panel" role="tabpanel">
          <pre id="pre-scrape-py">import requests&#10;&#10;data = requests.post(&#10;    'https://crawlee.sluxia.com/api/v1/scrape',&#10;    headers={&#10;        'Content-Type': 'application/json',&#10;        'X-Api-Key': 'YOUR_KEY'&#10;    },&#10;    json={&#10;        'url': 'https://stripe.com/docs',&#10;        'fit_markdown': True,&#10;        'chunk_size': 500,&#10;        'chunk_overlap': 80&#10;    }&#10;).json()</pre>
        </div>

        <!-- audit / curl -->
        <div id="code-audit-curl" class="code-panel" role="tabpanel">
          <pre id="pre-audit-curl">curl -X POST https://crawlee.sluxia.com/api/v1/security-audit \&#10;  -H 'Content-Type: application/json' \&#10;  -H 'X-Api-Key: YOUR_KEY' \&#10;  -d '{&#10;    "url": "https://example.com"&#10;  }'</pre>
        </div>
        <!-- audit / js -->
        <div id="code-audit-js" class="code-panel" role="tabpanel">
          <pre id="pre-audit-js">const res = await fetch('https://crawlee.sluxia.com/api/v1/security-audit', {&#10;  method: 'POST',&#10;  headers: {&#10;    'Content-Type': 'application/json',&#10;    'X-Api-Key': 'YOUR_KEY'&#10;  },&#10;  body: JSON.stringify({ url: 'https://example.com' })&#10;});&#10;const data = await res.json();</pre>
        </div>
        <!-- audit / python -->
        <div id="code-audit-py" class="code-panel" role="tabpanel">
          <pre id="pre-audit-py">import requests&#10;&#10;data = requests.post(&#10;    'https://crawlee.sluxia.com/api/v1/security-audit',&#10;    headers={&#10;        'Content-Type': 'application/json',&#10;        'X-Api-Key': 'YOUR_KEY'&#10;    },&#10;    json={'url': 'https://example.com'}&#10;).json()</pre>
        </div>

        <!-- dataset / curl -->
        <div id="code-dataset-curl" class="code-panel" role="tabpanel">
          <pre id="pre-dataset-curl">curl -X POST https://crawlee.sluxia.com/api/v1/dataset \&#10;  -H 'Content-Type: application/json' \&#10;  -H 'X-Api-Key: YOUR_KEY' \&#10;  -d '{&#10;    "url": "https://developers.cloudflare.com/fundamentals/",&#10;    "min_confidence": 0.85&#10;  }'</pre>
        </div>
        <!-- dataset / js -->
        <div id="code-dataset-js" class="code-panel" role="tabpanel">
          <pre id="pre-dataset-js">const res = await fetch('https://crawlee.sluxia.com/api/v1/dataset', {&#10;  method: 'POST',&#10;  headers: {&#10;    'Content-Type': 'application/json',&#10;    'X-Api-Key': 'YOUR_KEY'&#10;  },&#10;  body: JSON.stringify({&#10;    url: 'https://developers.cloudflare.com/fundamentals/',&#10;    min_confidence: 0.85&#10;  })&#10;});&#10;const data = await res.json();</pre>
        </div>
        <!-- dataset / python -->
        <div id="code-dataset-py" class="code-panel" role="tabpanel">
          <pre id="pre-dataset-py">import requests&#10;&#10;data = requests.post(&#10;    'https://crawlee.sluxia.com/api/v1/dataset',&#10;    headers={&#10;        'Content-Type': 'application/json',&#10;        'X-Api-Key': 'YOUR_KEY'&#10;    },&#10;    json={&#10;        'url': 'https://developers.cloudflare.com/fundamentals/',&#10;        'min_confidence': 0.85&#10;    }&#10;).json()</pre>
        </div>

      </section>

    </div>

    <!-- AUTH -->
    <section class="auth-section" id="auth" aria-labelledby="authHeading">
      <div class="page">
        <div class="auth-box">
          <div>
            <p class="section-label">Authentication</p>
            <h2 id="authHeading">One header. Every request.</h2>
            <p>
              Pass your key in the <code>X-Api-Key</code> header on every call. The health endpoint is always open for uptime monitoring. Everything else is gated.
            </p>
            <div class="auth-rule">
              <iconify-icon icon="lucide:check-circle" style="color: var(--color-success);" aria-hidden="true"></iconify-icon>
              <div>
                <strong>GET /api/v1/health</strong>
                Always open. No key required.
              </div>
            </div>
            <div class="auth-rule">
              <iconify-icon icon="lucide:key" aria-hidden="true"></iconify-icon>
              <div>
                <strong>POST /api/v1/scrape</strong>
                Requires X-Api-Key header.
              </div>
            </div>
            <div class="auth-rule">
              <iconify-icon icon="lucide:key" aria-hidden="true"></iconify-icon>
              <div>
                <strong>POST /api/v1/security-audit</strong>
                Requires X-Api-Key header.
              </div>
            </div>
            <div class="auth-rule">
              <iconify-icon icon="lucide:key" aria-hidden="true"></iconify-icon>
              <div>
                <strong>POST /api/v1/dataset</strong>
                Requires X-Api-Key header.
              </div>
            </div>
          </div>
          <div>
            <div class="auth-code">
              <pre><span class="code-comment"># Missing key</span>
HTTP 401 {"detail": "Missing X-Api-Key header"}

<span class="code-comment"># Wrong key</span>
HTTP 403 {"detail": "Invalid API key"}

<span class="code-comment"># Correct key</span>
HTTP 200 {"success": true, ...}</pre>
            </div>
          </div>
        </div>
      </div>
    </section>

  </main>

  <footer>
    <div class="footer-inner">
      <p>Crawlee is a private internal API. Requests require a valid API key.</p>
      <p style="font-size: 12px;">v3.0.0</p>
    </div>
  </footer>

  <script>
    // Theme
    (function () {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
      }
    })();

    document.getElementById('themeToggle').addEventListener('click', function () {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      document.getElementById('themeIcon').setAttribute('icon', isDark ? 'lucide:sun' : 'lucide:moon');
    });

    // Set correct icon on load
    document.addEventListener('DOMContentLoaded', function () {
      const isDark = document.documentElement.classList.contains('dark');
      document.getElementById('themeIcon').setAttribute('icon', isDark ? 'lucide:sun' : 'lucide:moon');
    });

    // Active nav on scroll
    (function () {
      var sections = ['endpoints', 'examples', 'auth'];
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var navLink = document.getElementById('nav-' + entry.target.id);
          if (navLink) {
            if (entry.isIntersecting) {
              document.querySelectorAll('.topbar-nav a').forEach(function (a) { a.classList.remove('active'); });
              navLink.classList.add('active');
            }
          }
        });
      }, { threshold: 0.3 });
      sections.forEach(function (id) {
        var el = document.getElementById(id);
        if (el) observer.observe(el);
      });
    })();

    // Code examples — endpoint + language state
    var currentEndpoint = 'scrape';
    var currentLang = 'curl';

    function showPanel() {
      document.querySelectorAll('.code-panel').forEach(function (p) { p.classList.remove('active'); });
      var id = 'code-' + currentEndpoint + '-' + currentLang;
      var panel = document.getElementById(id);
      if (panel) panel.classList.add('active');
    }

    function switchEndpoint(ep) {
      currentEndpoint = ep;
      document.querySelectorAll('.ep-btn').forEach(function (b) { b.classList.remove('active'); });
      document.getElementById('ep-' + ep).classList.add('active');
      showPanel();
    }

    function switchLang(lang) {
      currentLang = lang;
      document.querySelectorAll('.lang-tab').forEach(function (t) {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      document.getElementById('lt-' + lang).classList.add('active');
      document.getElementById('lt-' + lang).setAttribute('aria-selected', 'true');
      showPanel();
    }

    function copyCode() {
      var preId = 'pre-' + currentEndpoint + '-' + currentLang;
      var pre = document.getElementById(preId);
      if (!pre) return;
      var text = pre.innerText || pre.textContent;
      navigator.clipboard.writeText(text).then(function () {
        var btn = document.getElementById('copyBtn');
        btn.classList.add('copied');
        btn.innerHTML = '<iconify-icon icon="lucide:check" aria-hidden="true"></iconify-icon> Copied';
        setTimeout(function () {
          btn.classList.remove('copied');
          btn.innerHTML = '<iconify-icon icon="lucide:copy" aria-hidden="true"></iconify-icon> Copy';
        }, 2000);
      });
    }
  </script>

</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home():
    return HTMLResponse(content=HOME_HTML)

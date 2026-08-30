import re
from typing import Any, Callable, Dict, List, Tuple
from urllib.parse import urlparse

from selectolax.parser import HTMLParser


STRONG_SCORE = 0.45
MEDIUM_SCORE = 0.20
WEAK_SCORE = 0.08
CONTRADICTORY_SCORE = -0.35


SignalRule = Tuple[str, str, Callable[[str, Dict[str, str], HTMLParser], bool]]


DETECTORS: List[Dict[str, Any]] = [
    {
        "id": "wordpress_core",
        "platform_origin": "wordpress",
        "runtime_family": "cms",
        "framework": "wordpress",
        "render_mode": "server_rendered",
        "recommended_strategy": "cms_content",
        "rules": [
            ("strong", "wp-content path", lambda html, headers, tree: "wp-content" in html),
            ("strong", "wp-json link", lambda html, headers, tree: "wp-json" in html),
            ("medium", "wordpress generator meta", lambda html, headers, tree: "wordpress" in _meta_generator(tree)),
        ],
    },
    {
        "id": "shopify_storefront",
        "platform_origin": "shopify",
        "runtime_family": "commerce",
        "framework": "shopify",
        "render_mode": "server_rendered",
        "recommended_strategy": "commerce_content",
        "rules": [
            ("strong", "shopify cdn asset", lambda html, headers, tree: "cdn.shopify.com" in html),
            ("strong", "shopify global", lambda html, headers, tree: "Shopify." in html),
            ("medium", "shopify theme marker", lambda html, headers, tree: "shopify-theme" in html.lower() or "shopify.theme" in html.lower()),
        ],
    },
    {
        "id": "webflow_site",
        "platform_origin": "webflow",
        "runtime_family": "no_code_design_platform",
        "framework": "webflow",
        "render_mode": "static",
        "recommended_strategy": "static_marketing",
        "rules": [
            ("strong", "webflow page marker", lambda html, headers, tree: "data-wf-page" in html),
            ("strong", "webflow site marker", lambda html, headers, tree: "data-wf-site" in html),
            ("medium", "webflow asset path", lambda html, headers, tree: "webflow" in html.lower()),
        ],
    },
    {
        "id": "framer_site",
        "platform_origin": "framer",
        "runtime_family": "no_code_design_platform",
        "framework": "framer",
        "render_mode": "static",
        "recommended_strategy": "static_marketing",
        "rules": [
            ("strong", "framer asset domain", lambda html, headers, tree: "framerusercontent.com" in html or "framer.app" in html),
            ("strong", "framer script marker", lambda html, headers, tree: "framer" in html.lower() and "_framer" in html.lower()),
            ("medium", "framer meta marker", lambda html, headers, tree: "framer" in _meta_generator(tree) or "framer" in _canonical(tree)),
        ],
    },
    {
        "id": "wix_site",
        "platform_origin": "wix",
        "runtime_family": "no_code_platform",
        "framework": "wix",
        "render_mode": "static",
        "recommended_strategy": "static_marketing",
        "rules": [
            ("strong", "wixstatic asset", lambda html, headers, tree: "wixstatic.com" in html),
            ("strong", "wix runtime marker", lambda html, headers, tree: "viewerModel" in html or "wix-code" in html.lower()),
            ("medium", "wix platform marker", lambda html, headers, tree: "wix" in _canonical(tree) or "wix" in _meta_generator(tree)),
        ],
    },
    {
        "id": "squarespace_site",
        "platform_origin": "squarespace",
        "runtime_family": "no_code_platform",
        "framework": "squarespace",
        "render_mode": "server_rendered",
        "recommended_strategy": "static_marketing",
        "rules": [
            ("strong", "squarespace static asset", lambda html, headers, tree: "static.squarespace.com" in html or "squarespace-cdn.com" in html),
            ("medium", "squarespace generator", lambda html, headers, tree: "squarespace" in _meta_generator(tree)),
            ("medium", "squarespace marker", lambda html, headers, tree: "sqs-" in html.lower()),
        ],
    },
    {
        "id": "nextjs_site",
        "platform_origin": "nextjs",
        "runtime_family": "react_meta_framework",
        "framework": "nextjs",
        "render_mode": "ssr_or_static",
        "recommended_strategy": "docs_content",
        "rules": [
            ("strong", "__NEXT_DATA__ marker", lambda html, headers, tree: "__NEXT_DATA__" in html),
            ("strong", "_next asset path", lambda html, headers, tree: "/_next/" in html),
            ("medium", "next header", lambda html, headers, tree: any("next" in f"{k}:{v}".lower() for k, v in headers.items())),
        ],
    },
    {
        "id": "nuxt_site",
        "platform_origin": "nuxt",
        "runtime_family": "vue_meta_framework",
        "framework": "nuxt",
        "render_mode": "ssr_or_static",
        "recommended_strategy": "static_marketing",
        "rules": [
            ("strong", "__NUXT__ marker", lambda html, headers, tree: "__NUXT__" in html),
            ("strong", "_nuxt asset path", lambda html, headers, tree: "/_nuxt/" in html),
            ("medium", "nuxt marker", lambda html, headers, tree: "nuxt" in html.lower()),
        ],
    },
    {
        "id": "astro_site",
        "platform_origin": "astro",
        "runtime_family": "static_site_generator",
        "framework": "astro",
        "render_mode": "static",
        "recommended_strategy": "static_marketing",
        "rules": [
            ("strong", "astro asset path", lambda html, headers, tree: "/_astro/" in html),
            ("medium", "astro island marker", lambda html, headers, tree: "astro-island" in html.lower()),
            ("medium", "astro marker", lambda html, headers, tree: "astro" in _meta_generator(tree) or "astro" in html.lower()),
        ],
    },
    {
        "id": "angular_app",
        "platform_origin": "angular",
        "runtime_family": "spa_framework",
        "framework": "angular",
        "render_mode": "spa_or_ssr",
        "recommended_strategy": "spa_shell",
        "rules": [
            ("strong", "ng-version marker", lambda html, headers, tree: "ng-version" in html),
            ("medium", "angular runtime", lambda html, headers, tree: "angular" in html.lower()),
            ("medium", "app-root element", lambda html, headers, tree: "<app-root" in html.lower()),
        ],
    },
    {
        "id": "docusaurus_docs",
        "platform_origin": "docusaurus",
        "runtime_family": "docs_framework",
        "framework": "docusaurus",
        "render_mode": "static",
        "recommended_strategy": "docs_content",
        "rules": [
            ("strong", "docusaurus asset path", lambda html, headers, tree: "docusaurus" in html.lower()),
            ("medium", "docs sidebar pattern", lambda html, headers, tree: "theme-doc-sidebar" in html.lower()),
            ("medium", "docs article pattern", lambda html, headers, tree: "theme-doc-markdown" in html.lower()),
        ],
    },
    {
        "id": "vitepress_docs",
        "platform_origin": "vitepress",
        "runtime_family": "docs_framework",
        "framework": "vitepress",
        "render_mode": "static",
        "recommended_strategy": "docs_content",
        "rules": [
            ("strong", "vitepress asset path", lambda html, headers, tree: "vitepress" in html.lower()),
            ("medium", "vp-doc marker", lambda html, headers, tree: "vp-doc" in html.lower()),
            ("medium", "vitepress nav marker", lambda html, headers, tree: "vp-nav" in html.lower()),
        ],
    },
    {
        "id": "mkdocs_material",
        "platform_origin": "mkdocs",
        "runtime_family": "docs_generator",
        "framework": "mkdocs",
        "render_mode": "static",
        "recommended_strategy": "docs_content",
        "rules": [
            ("strong", "mkdocs marker", lambda html, headers, tree: "mkdocs" in html.lower()),
            ("medium", "material marker", lambda html, headers, tree: "material/" in html.lower() or "md-content" in html.lower()),
            ("medium", "mkdocs generator", lambda html, headers, tree: "mkdocs" in _meta_generator(tree)),
        ],
    },
    {
        "id": "lovable_built",
        "platform_origin": "lovable",
        "runtime_family": "ai_builder",
        "framework": "lovable",
        "render_mode": "static_or_spa",
        "recommended_strategy": "ai_builder_marketing",
        "rules": [
            ("strong", "lovable domain", lambda html, headers, tree: "lovable.dev" in html or "lovable.app" in html or "lovable.dev" in headers.get("x-detector-host", "")),
            ("medium", "lovable branding", lambda html, headers, tree: "lovable" in html.lower()),
            ("medium", "lovable builder phrasing", lambda html, headers, tree: "build something lovable" in html.lower()),
            ("weak", "ai app builder phrasing", lambda html, headers, tree: "build apps and websites" in html.lower()),
        ],
    },
    {
        "id": "bolt_built",
        "platform_origin": "bolt",
        "runtime_family": "ai_builder",
        "framework": "bolt",
        "render_mode": "static_or_spa",
        "recommended_strategy": "docs_content",
        "rules": [
            ("strong", "bolt domain", lambda html, headers, tree: "bolt.new" in html or "support.bolt.new" in html or "bolt.new" in headers.get("x-detector-host", "")),
            ("medium", "bolt branding", lambda html, headers, tree: "bolt" in html.lower()),
            ("medium", "bolt doc title", lambda html, headers, tree: "introduction to bolt" in html.lower()),
            ("weak", "documentation index wording", lambda html, headers, tree: "documentation index" in html.lower()),
        ],
    },
    {
        "id": "php_server_rendered",
        "platform_origin": "php",
        "runtime_family": "traditional_server_rendered",
        "framework": "php",
        "render_mode": "server_rendered",
        "recommended_strategy": "cms_content",
        "rules": [
            ("medium", "php powered by header", lambda html, headers, tree: "php" in headers.get("x-powered-by", "").lower()),
            ("weak", "php query path", lambda html, headers, tree: ".php" in html.lower()),
            ("contradictory", "next strong contradiction", lambda html, headers, tree: "__NEXT_DATA__" in html or "/_next/" in html),
        ],
    },
]


def _meta_generator(tree: HTMLParser) -> str:
    generator = tree.css_first('meta[name="generator"]')
    return (generator.attributes.get("content") or "").lower() if generator else ""


def _canonical(tree: HTMLParser) -> str:
    canonical = tree.css_first('link[rel="canonical"]')
    return (canonical.attributes.get("href") or "").lower() if canonical else ""


def _score_value(weight: str) -> float:
    if weight == "strong":
        return STRONG_SCORE
    if weight == "medium":
        return MEDIUM_SCORE
    if weight == "weak":
        return WEAK_SCORE
    return CONTRADICTORY_SCORE


def detect_site_type(target_url: str, html_text: str, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    headers["x-detector-host"] = urlparse(target_url).netloc.lower()
    tree = HTMLParser(html_text)
    results = []

    for detector in DETECTORS:
        score = 0.0
        signals: List[str] = []
        for weight, label, predicate in detector["rules"]:
            if predicate(html_text, headers, tree):
                score += _score_value(weight)
                if weight != "contradictory":
                    signals.append(label)
        if score > 0:
            results.append(
                {
                    **{k: v for k, v in detector.items() if k != "rules"},
                    "confidence": round(score, 2),
                    "signals": signals,
                }
            )

    results.sort(key=lambda item: item["confidence"], reverse=True)
    if not results or results[0]["confidence"] <= 0.55:
        return {
            "platform_origin": "unknown",
            "runtime_family": "unknown",
            "framework": "unknown",
            "render_mode": "unknown",
            "confidence": 0.0,
            "matched_detectors": [],
            "signals": _generic_signals(target_url, html_text, tree),
            "recommended_strategy": "generic_html",
            "secondary_matches": [],
        }

    primary = results[0]
    secondary = [
        match["id"]
        for match in results[1:]
        if match["confidence"] >= 0.45 and primary["confidence"] - match["confidence"] <= 0.10
    ]
    return {
        "platform_origin": primary["platform_origin"],
        "runtime_family": primary["runtime_family"],
        "framework": primary["framework"],
        "render_mode": primary["render_mode"],
        "confidence": primary["confidence"],
        "matched_detectors": [primary["id"], *secondary],
        "signals": primary["signals"],
        "recommended_strategy": primary["recommended_strategy"],
        "secondary_matches": secondary,
    }


def _generic_signals(target_url: str, html_text: str, tree: HTMLParser) -> List[str]:
    signals = []
    hostname = urlparse(target_url).netloc
    if hostname:
        signals.append(f"host:{hostname}")
    if tree.css_first("article"):
        signals.append("article element present")
    if tree.css_first("main"):
        signals.append("main element present")
    if re.search(r"<h[1-3][^>]*>", html_text, re.I):
        signals.append("heading structure present")
    return signals[:3]

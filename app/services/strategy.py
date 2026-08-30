from typing import Any, Dict, List

import trafilatura
from selectolax.parser import HTMLParser

from .security import normalize_text


FALLBACK_CHAINS = {
    "generic_html": ["default_extract", "metadata_fusion", "low_content_verdict"],
    "static_marketing": ["default_extract", "section_heading_fusion", "metadata_fusion", "low_content_verdict"],
    "cms_content": ["default_extract", "main_region_extract", "section_heading_fusion", "metadata_fusion", "low_content_verdict"],
    "docs_content": ["default_extract", "docs_main_extract", "heading_tree_extract", "metadata_fusion", "low_content_verdict"],
    "commerce_content": ["default_extract", "product_region_extract", "metadata_fusion", "low_content_verdict"],
    "spa_shell": ["default_extract", "shell_text_extract", "metadata_fusion", "link_graph_summary", "low_content_verdict"],
    "ai_builder_marketing": ["default_extract", "section_heading_fusion", "metadata_fusion", "low_content_verdict"],
}


def run_scrape_strategy(
    tree: HTMLParser,
    html_text: str,
    site_detection: Dict[str, Any],
    fit_markdown: bool,
    internal_links_count: int,
) -> Dict[str, Any]:
    strategy_name = site_detection["recommended_strategy"]
    attempts = FALLBACK_CHAINS[strategy_name]
    extraction_result = None
    diagnostics = None

    for index, attempt in enumerate(attempts):
        extraction_result = _run_attempt(attempt, tree, html_text, fit_markdown, internal_links_count)
        diagnostics = _build_diagnostics(
            attempted_strategies=attempts[: index + 1],
            final_strategy=attempt,
            extraction_result=extraction_result,
            internal_links_count=internal_links_count,
            fallback_used=index > 0,
        )
        if diagnostics["content_quality"] == "good" or attempt == "low_content_verdict":
            return {
                "content": extraction_result,
                "diagnostics": diagnostics,
            }

    return {
        "content": extraction_result or {"markdown": "", "chunks": []},
        "diagnostics": diagnostics or _build_diagnostics(["low_content_verdict"], "low_content_verdict", {"markdown": ""}, internal_links_count, False),
    }


def _run_attempt(
    attempt: str,
    tree: HTMLParser,
    html_text: str,
    fit_markdown: bool,
    internal_links_count: int,
) -> Dict[str, Any]:
    if attempt == "default_extract":
        markdown = (
            trafilatura.extract(
                html_text,
                output_format="markdown",
                include_links=not fit_markdown,
                include_images=not fit_markdown,
            )
            or ""
        )
        return {"markdown": markdown}

    if attempt == "main_region_extract":
        return {
            "markdown": _extract_from_selectors(
                tree,
                ["main", "article", "[role='main']", ".post-content", ".entry-content", ".article-content"],
            )
        }

    if attempt == "docs_main_extract":
        return {
            "markdown": _extract_from_selectors(
                tree,
                [
                    ".theme-doc-markdown",
                    ".VPContent",
                    ".VPHome",
                    ".VPHero",
                    ".vp-doc",
                    ".md-content",
                    "main article",
                    "main",
                    "article",
                ],
            )
        }

    if attempt == "product_region_extract":
        return {"markdown": _extract_product_region(tree)}

    if attempt == "section_heading_fusion":
        return {"markdown": _extract_section_heading_fusion(tree)}

    if attempt == "heading_tree_extract":
        return {"markdown": _extract_heading_tree(tree)}

    if attempt == "metadata_fusion":
        return {"markdown": _extract_metadata_fusion(tree)}

    if attempt == "shell_text_extract":
        return {"markdown": _extract_shell_text(tree)}

    if attempt == "link_graph_summary":
        return {"markdown": f"Internal links discovered: {internal_links_count}"}

    return {"markdown": ""}


def _extract_from_first(tree: HTMLParser, selector: str) -> str:
    node = tree.css_first(selector)
    return normalize_text(node.text(separator=" ", strip=True)).strip() if node else ""


def _extract_from_selectors(tree: HTMLParser, selectors: List[str], min_chars: int = 120) -> str:
    best_text = ""
    for selector in selectors:
        for node in tree.css(selector):
            text = normalize_text(node.text(separator=" ", strip=True)).strip()
            if len(text) >= min_chars:
                return text
            if len(text) > len(best_text):
                best_text = text
    return best_text


def _extract_section_heading_fusion(tree: HTMLParser) -> str:
    parts: List[str] = []
    for node in tree.css("h1, h2, h3, section p, main p"):
        text = normalize_text(node.text(separator=" ", strip=True)).strip()
        if text and len(text) > 20:
            parts.append(text)
        if len(parts) >= 20:
            break
    return "\n\n".join(parts)


def _extract_heading_tree(tree: HTMLParser) -> str:
    parts: List[str] = []
    for node in tree.css("h1, h2, h3, h4"):
        text = normalize_text(node.text(separator=" ", strip=True)).strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _extract_metadata_fusion(tree: HTMLParser) -> str:
    parts: List[str] = []
    for selector in ["title", 'meta[name="description"]', 'meta[property="og:title"]', 'meta[property="og:description"]']:
        node = tree.css_first(selector)
        if not node:
            continue
        value = node.text(separator=" ", strip=True) if node.tag == "title" else node.attributes.get("content", "")
        normalized = normalize_text(value).strip()
        if normalized:
            parts.append(normalized)
    return "\n\n".join(dict.fromkeys(parts))


def _extract_product_region(tree: HTMLParser) -> str:
    parts: List[str] = []
    for selector in ["h1", '[class*="price"]', '[data-testid*="price"]', "main p", '[class*="product"] p']:
        for node in tree.css(selector):
            if len(parts) >= 20:
                break
            text = normalize_text(node.text(separator=" ", strip=True)).strip()
            if text and (selector == "h1" or len(text) > 12):
                parts.append(text)
    return "\n\n".join(dict.fromkeys(parts))


def _extract_shell_text(tree: HTMLParser) -> str:
    texts = []
    for selector in ["title", "h1", "h2", "button", "nav a"]:
        for node in tree.css(selector):
            if len(texts) >= 20:
                break
            text = normalize_text(node.text(separator=" ", strip=True)).strip()
            if text:
                texts.append(text)
    return "\n".join(dict.fromkeys(texts))


def _build_diagnostics(
    attempted_strategies: List[str],
    final_strategy: str,
    extraction_result: Dict[str, Any],
    internal_links_count: int,
    fallback_used: bool,
) -> Dict[str, Any]:
    markdown = extraction_result.get("markdown", "")
    visible_text_chars = len(markdown)
    markdown_word_count = len(markdown.split())
    headings_found = sum(1 for line in markdown.splitlines() if line.strip())

    thin = visible_text_chars < 400 and markdown_word_count < 80
    shell_like = headings_found == 0 and internal_links_count < 5
    if not thin:
        content_quality = "good"
        failure_reason = None
    else:
        content_quality = "low"
        if final_strategy in {"shell_text_extract", "link_graph_summary", "low_content_verdict"}:
            failure_reason = "js_dependent_shell"
        elif internal_links_count >= 5 and headings_found == 0:
            failure_reason = "navigation_heavy_page"
        elif visible_text_chars == 0:
            failure_reason = "extractor_low_yield"
        elif shell_like:
            failure_reason = "sparse_page"
        else:
            failure_reason = "extractor_low_yield"

    return {
        "attempted_strategies": attempted_strategies,
        "final_strategy": final_strategy,
        "content_quality": content_quality,
        "visible_text_chars": visible_text_chars,
        "markdown_chars": len(markdown),
        "headings_found": headings_found,
        "internal_links_found": internal_links_count,
        "fallback_used": fallback_used,
        "failure_reason": failure_reason,
    }

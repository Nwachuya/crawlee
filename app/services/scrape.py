from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import trafilatura
from selectolax.parser import HTMLParser

from .detection import detect_site_type
from .security import normalize_text, scan_security_threats
from .strategy import run_scrape_strategy


def extract_markdown(html_text: str, fit_markdown: bool) -> str:
    return (
        trafilatura.extract(
            html_text,
            output_format="markdown",
            include_links=not fit_markdown,
            include_images=not fit_markdown,
        )
        or ""
    )


def build_chunks(markdown_content: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    chunks: List[str] = []
    if chunk_size <= 0:
        return chunks

    start = 0
    step = chunk_size - chunk_overlap
    while start < len(markdown_content):
        chunks.append(markdown_content[start : start + chunk_size])
        start += step
    return chunks


def extract_custom_selectors(tree: HTMLParser, selectors: Optional[Dict[str, str]]) -> Dict[str, List[str]]:
    custom_selectors: Dict[str, List[str]] = {}
    if not selectors:
        return custom_selectors

    for key, selector in selectors.items():
        custom_selectors[key] = [node.text().strip() for node in tree.css(selector)]
    return custom_selectors


def extract_images(tree: HTMLParser, target_url: str) -> List[Dict[str, str]]:
    images: List[Dict[str, str]] = []
    seen_sources = set()

    for img in tree.css("img"):
        src = img.attributes.get("src")
        if not src:
            continue
        full_src = urljoin(target_url, src)
        if full_src in seen_sources:
            continue
        seen_sources.add(full_src)
        images.append(
            {
                "src": full_src,
                "alt": normalize_text(img.attributes.get("alt") or "").strip(),
            }
        )

    return images


def extract_links(tree: HTMLParser, target_url: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    parsed_target = urlparse(target_url)
    internal_links: List[Dict[str, str]] = []
    external_links: List[Dict[str, str]] = []
    seen_links = set()

    for anchor in tree.css("a[href]"):
        href = (anchor.attributes.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue

        full_url = urljoin(target_url, href)
        text = normalize_text(anchor.text()).strip()
        link_key = (full_url, text)
        if link_key in seen_links:
            continue
        seen_links.add(link_key)

        link_obj = {"href": full_url, "text": text}
        if urlparse(full_url).netloc == parsed_target.netloc:
            internal_links.append(link_obj)
        else:
            external_links.append(link_obj)

    return internal_links, external_links


def build_scrape_response(
    target_url: str,
    html_text: str,
    headers: Optional[Dict[str, str]],
    chunk_size: int,
    chunk_overlap: int,
    selectors: Optional[Dict[str, str]],
    fit_markdown: bool,
    sanitize_injections: bool,
) -> Dict[str, Any]:
    tree = HTMLParser(html_text)
    custom_selectors = extract_custom_selectors(tree, selectors)
    images = extract_images(tree, target_url)
    internal_links, external_links = extract_links(tree, target_url)
    site_detection = detect_site_type(target_url, html_text, headers=headers or {})
    strategy_result = run_scrape_strategy(
        tree=tree,
        html_text=html_text,
        site_detection=site_detection,
        fit_markdown=fit_markdown,
        internal_links_count=len(internal_links),
    )
    markdown_content = strategy_result["content"]["markdown"]
    chunks = build_chunks(markdown_content, chunk_size, chunk_overlap)

    response: Dict[str, Any] = {
        "success": True,
        "url": target_url,
        "metrics": {
            "word_count": len(markdown_content.split()),
            "estimated_tokens": max(1, len(markdown_content) // 4),
        },
        "content": {"markdown": markdown_content, "chunks": chunks},
        "extracted_data": {"custom_selectors": custom_selectors},
        "media": {"images": images},
        "links": {"internal": internal_links, "external": external_links},
        "site_detection": site_detection,
        "extraction_diagnostics": strategy_result["diagnostics"],
    }

    if sanitize_injections:
        response["security_audit"] = scan_security_threats(tree, html_text)

    return response

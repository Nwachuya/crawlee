import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from curl_cffi.requests import AsyncSession
import trafilatura
from selectolax.parser import HTMLParser

app = FastAPI(
    title="AI-Native Ultra-Light Scraper & Security Engine",
    version="2.0.0"
)

class ScrapeRequest(BaseModel):
    url: HttpUrl
    impersonate: Optional[str] = "chrome120"
    chunk_size: Optional[int] = 0           # 0 means no chunking
    chunk_overlap: Optional[int] = 100
    selectors: Optional[Dict[str, str]] = None  # Custom CSS extraction
    fit_markdown: Optional[bool] = False     # Strip noise for dense context
    sanitize_injections: Optional[bool] = True

# Known prompt injection regex patterns
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts)", re.I),
    re.compile(r"system\s+prompt\s+(override|injection)", re.I),
    re.compile(r"disregard\s+(prior|previous)\s+directives", re.I),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(dan|developer|god)\s+mode", re.I),
    re.compile(r"new\s+system\s+instruction:", re.I),
    re.compile(r"print\s+your\s+(initial|system)\s+prompt", re.I),
    re.compile(r"override\s+safety\s+guidelines", re.I)
]

ZERO_WIDTH_REGEX = re.compile(r"[\u200B-\u200D\uFEFF]")

def detect_security_threats(tree: HTMLParser, raw_html: str) -> Dict[str, Any]:
    """Feature H: Scans for hidden CSS elements, zero-width spaces, and prompt injections."""
    threats = []
    hidden_count = 0
    prompt_injection_detected = False

    # 1. Zero-width character scan
    zero_width_matches = ZERO_WIDTH_REGEX.findall(raw_html)
    if zero_width_matches:
        threats.append({
            "type": "zero_width_characters",
            "count": len(zero_width_matches),
            "detail": "Zero-width hidden characters detected in DOM."
        })

    # 2. Hidden CSS & Attribute Scanning
    hidden_selectors = [
        '[style*="display:none"]', '[style*="display: none"]',
        '[style*="visibility:hidden"]', '[style*="visibility: hidden"]',
        '[style*="opacity:0"]', '[style*="opacity: 0"]',
        '[style*="font-size:0"]', '[style*="font-size: 0"]',
        '[aria-hidden="true"]', '[hidden]'
    ]
    
    hidden_texts = []
    for selector in hidden_selectors:
        for node in tree.css(selector):
            text = node.text().strip()
            if text:
                hidden_count += 1
                hidden_texts.append(text)
                threats.append({
                    "type": "hidden_css_element",
                    "selector": selector,
                    "snippet": text[:100]
                })

    # 3. Prompt Injection Pattern Match across page text and hidden elements
    full_text = tree.text()
    scannable_text = full_text + " " + " ".join(hidden_texts)

    for pattern in INJECTION_PATTERNS:
        if pattern.search(scannable_text):
            prompt_injection_detected = True
            threats.append({
                "type": "prompt_injection_pattern",
                "pattern": pattern.pattern,
                "detail": "Adversarial prompt injection pattern detected."
            })

    return {
        "is_suspicious": len(threats) > 0,
        "prompt_injection_detected": prompt_injection_detected,
        "hidden_elements_count": hidden_count,
        "threats": threats
    }

def sanitize_content(markdown: str) -> str:
    """Removes detected prompt injection patterns from output markdown."""
    clean_md = markdown
    for pattern in INJECTION_PATTERNS:
        clean_md = pattern.sub("[REDACTED_PROMPT_INJECTION]", clean_md)
    return clean_md

def create_chunks(text: str, size: int, overlap: int) -> List[str]:
    """Feature B: Native token/character chunker."""
    if size <= 0 or not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + size, text_len)
        chunks.append(text[start:end])
        start += size - overlap
    return chunks

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/scrape")
async def scrape(payload: ScrapeRequest):
    target_url = str(payload.url)
    parsed_target = urlparse(target_url)
    target_domain = parsed_target.netloc

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    # Feature A: TLS Impersonation using curl_cffi
    async with AsyncSession(impersonate=payload.impersonate) as session:
        try:
            response = await session.get(target_url, headers=headers, timeout=15)
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail="Target URL returned an error.")
            html_text = response.text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Request failed: {str(e)}")

    tree = HTMLParser(html_text)

    # Feature H: Prompt Injection & Threat Detection
    security_audit = detect_security_threats(tree, html_text)

    # Base Markdown extraction via Trafilatura
    markdown_content = trafilatura.extract(
        html_text,
        output_format="markdown",
        include_links=not payload.fit_markdown,
        include_images=not payload.fit_markdown
    ) or ""

    if payload.sanitize_injections and security_audit["prompt_injection_detected"]:
        markdown_content = sanitize_content(markdown_content)

    # Feature C: Token estimation heuristic (~4 chars per token)
    word_count = len(markdown_content.split())
    estimated_tokens = len(markdown_content) // 4

    # Feature F: Quality & Density Scoring
    html_length = len(html_text)
    text_length = len(markdown_content)
    density_score = round(text_length / html_length, 4) if html_length > 0 else 0.0

    # Feature B: Chunking
    chunks = create_chunks(markdown_content, payload.chunk_size, payload.chunk_overlap)

    # Feature D: Dynamic CSS Selectors Extraction
    custom_selector_data = {}
    if payload.selectors:
        for key, selector in payload.selectors.items():
            nodes = tree.css(selector)
            custom_selector_data[key] = [node.text().strip() for node in nodes]

    # Feature G: Code Blocks & Tables Extraction
    code_blocks = [code.text().strip() for code in tree.css("pre code")]
    tables = [table.text().strip() for table in tree.css("table")]

    # Extract Page Meta Information
    title_tag = tree.css_first("title")
    meta_desc = tree.css_first('meta[name="description"]')
    title = title_tag.text().strip() if title_tag else ""
    description = meta_desc.attributes.get("content", "").strip() if meta_desc else ""

    og_metadata = {}
    for meta in tree.css('meta[property^="og:"]'):
        prop = meta.attributes.get("property")
        val = meta.attributes.get("content")
        if prop and val:
            og_metadata[prop] = val

    # Media Extraction
    images = []
    for img in tree.css("img"):
        src = img.attributes.get("src") or img.attributes.get("data-src")
        if src:
            images.append({
                "src": urljoin(target_url, src),
                "alt": img.attributes.get("alt", "").strip(),
                "title": img.attributes.get("title", "").strip() or None
            })

    # Links Extraction (Internal vs External)
    internal_links = []
    external_links = []
    seen_links = set()

    for a in tree.css("a[href]"):
        href = a.attributes.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        full_url = urljoin(target_url, href)
        if full_url in seen_links:
            continue
        seen_links.add(full_url)

        link_domain = urlparse(full_url).netloc
        link_obj = {"href": full_url, "text": a.text().strip()}

        if link_domain == target_domain:
            internal_links.append(link_obj)
        else:
            external_links.append(link_obj)

    return {
        "success": True,
        "url": target_url,
        "status_code": response.status_code,
        "security_audit": security_audit,
        "metrics": {
            "word_count": word_count,
            "estimated_tokens": estimated_tokens,
            "content_density_score": density_score
        },
        "metadata": {
            "title": title,
            "description": description,
            "open_graph": og_metadata
        },
        "content": {
            "markdown": markdown_content,
            "chunks": chunks
        },
        "extracted_data": {
            "custom_selectors": custom_selector_data,
            "code_blocks": code_blocks,
            "tables": tables
        },
        "media": {
            "images": images
        },
        "links": {
            "internal": internal_links,
            "external": external_links
        }
    }

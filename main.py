from app.application import app
from app.schemas import AuditRequest, BaseRequest, DatasetRequest, ScrapeRequest
from app.services.dataset import (
    ENTITY_REGEX,
    build_export_formats,
    classify_complexity,
    extract_sections_from_markdown,
    generate_question,
)
from app.services.detection import DETECTORS, detect_site_type
from app.services.fetch import fetch_html, fetch_page
from app.services.scrape import build_chunks, build_scrape_response, extract_custom_selectors, extract_images, extract_links
from app.services.security import (
    COMMENT_REGEX,
    HIDDEN_SELECTORS,
    INJECTION_PATTERNS,
    SECRET_PATTERNS,
    ZERO_WIDTH_REGEX,
    collect_secret_findings,
    normalize_text,
    scan_security_threats,
    should_flag_hidden_text,
)
from app.services.strategy import FALLBACK_CHAINS, run_scrape_strategy

__all__ = [
    "app",
    "AuditRequest",
    "BaseRequest",
    "DatasetRequest",
    "ScrapeRequest",
    "COMMENT_REGEX",
    "DETECTORS",
    "ENTITY_REGEX",
    "FALLBACK_CHAINS",
    "HIDDEN_SELECTORS",
    "INJECTION_PATTERNS",
    "SECRET_PATTERNS",
    "ZERO_WIDTH_REGEX",
    "build_chunks",
    "build_export_formats",
    "build_scrape_response",
    "classify_complexity",
    "collect_secret_findings",
    "detect_site_type",
    "extract_custom_selectors",
    "extract_images",
    "extract_links",
    "extract_sections_from_markdown",
    "fetch_html",
    "fetch_page",
    "generate_question",
    "normalize_text",
    "run_scrape_strategy",
    "scan_security_threats",
    "should_flag_hidden_text",
]

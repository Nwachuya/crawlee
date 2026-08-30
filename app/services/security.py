import html
import re
import unicodedata
from typing import Any, Dict, List

from selectolax.parser import HTMLParser


INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts)", re.I),
    re.compile(r"system\s+prompt\s+(override|injection)", re.I),
    re.compile(r"disregard\s+(prior|previous)\s+directives", re.I),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(dan|developer|god)\s+mode", re.I),
    re.compile(r"new\s+system\s+instruction:", re.I),
    re.compile(r"print\s+your\s+(initial|system)\s+prompt", re.I),
    re.compile(r"override\s+safety\s+guidelines", re.I),
    re.compile(r"ignore\s+prior\s+rules", re.I),
    re.compile(r"override\s+system\s+prompt", re.I),
    re.compile(r"output\s+(all\s+)?(environment\s+variables|env)\b", re.I),
    re.compile(r"exfiltrate\s+(page\s+contents|database\s+keys|data)\b", re.I),
    re.compile(r"reveal\s+your\s+system\s+prompt", re.I),
]

ZERO_WIDTH_REGEX = re.compile(r"[\u200B-\u200D\uFEFF]")
COMMENT_REGEX = re.compile(r"<!--(.*?)-->", re.S)

SECRET_PATTERNS = [
    ("stripe_live_key", re.compile(r"\bsk_live_[A-Za-z0-9]+\b")),
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]+\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9-]+\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+\b", re.I)),
    ("generic_secret_assignment", re.compile(r"\b(?:api[_-]?key|secret|token)\b\s*[:=]\s*[\"']?[A-Za-z0-9._\-]{16,}", re.I)),
]

HIDDEN_SELECTORS = [
    '[style*="display:none"]',
    '[style*="display: none"]',
    '[style*="visibility:hidden"]',
    '[style*="visibility: hidden"]',
    '[style*="opacity:0"]',
    '[style*="opacity: 0"]',
    '[style*="font-size:0"]',
    '[style*="font-size: 0"]',
    '[style*="left:-9999px"]',
    '[style*="left: -9999px"]',
    '[style*="top:-9999px"]',
    '[style*="top: -9999px"]',
    '[style*="position:absolute"]',
    '[style*="position: absolute"]',
    '[aria-hidden="true"]',
    '[hidden]',
]

ATTRIBUTE_CARRIER_SELECTORS = "meta, img, input, textarea, button, a"


def should_flag_hidden_text(selector: str, text: str) -> bool:
    clean = " ".join(text.split()).strip()
    if not clean:
        return False
    if any(pattern.search(clean) for pattern in INJECTION_PATTERNS):
        return True
    if selector in ('[aria-hidden="true"]', "[hidden]"):
        return False

    has_letters = bool(re.search(r"[A-Za-z]", clean))
    has_enough_words = len(re.findall(r"\w+", clean)) >= 4
    return has_letters and has_enough_words and len(clean) >= 20


def normalize_text(text: str) -> str:
    decoded = html.unescape(text or "")
    normalized = unicodedata.normalize("NFKC", decoded)
    return ZERO_WIDTH_REGEX.sub(" ", normalized)


def collect_secret_findings(text: str, source_type: str, source_hint: str = "") -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for secret_type, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                {
                    "type": "secret_pattern",
                    "secret_type": secret_type,
                    "source": source_type,
                    "location": source_hint,
                    "snippet": match.group(0)[:100],
                }
            )
    return findings


def scan_security_threats(tree: HTMLParser, raw_html: str) -> Dict[str, Any]:
    threats: List[Dict[str, Any]] = []
    hidden_count = 0
    prompt_injection_detected = False

    zero_width_matches = ZERO_WIDTH_REGEX.findall(raw_html)
    if zero_width_matches:
        threats.append(
            {
                "type": "zero_width_characters",
                "count": len(zero_width_matches),
                "detail": "Zero-width characters detected.",
            }
        )

    hidden_texts = []
    seen_hidden_snippets = set()
    for selector in HIDDEN_SELECTORS:
        for node in tree.css(selector):
            normalized = " ".join(normalize_text(node.text().strip()).split())
            if normalized and should_flag_hidden_text(selector, normalized) and normalized not in seen_hidden_snippets:
                seen_hidden_snippets.add(normalized)
                hidden_count += 1
                hidden_texts.append(normalized)
                threats.append(
                    {
                        "type": "hidden_css_element",
                        "selector": selector,
                        "snippet": normalized[:100],
                    }
                )
                if any(pattern.search(normalized) for pattern in INJECTION_PATTERNS):
                    prompt_injection_detected = True

    for comment in COMMENT_REGEX.findall(raw_html):
        normalized = " ".join(normalize_text(comment).split())
        if any(pattern.search(normalized) for pattern in INJECTION_PATTERNS):
            prompt_injection_detected = True
            threats.append({"type": "comment_injection", "snippet": normalized[:100]})

    for node in tree.css(ATTRIBUTE_CARRIER_SELECTORS):
        for attr_name, attr_value in node.attributes.items():
            if not attr_value:
                continue
            normalized = " ".join(normalize_text(attr_value).split())
            if any(pattern.search(normalized) for pattern in INJECTION_PATTERNS):
                prompt_injection_detected = True
                threats.append(
                    {
                        "type": "attribute_injection",
                        "tag": node.tag,
                        "attribute": attr_name,
                        "snippet": normalized[:100],
                    }
                )
            threats.extend(collect_secret_findings(normalized, "attribute", f"{node.tag}[{attr_name}]"))

    for script in tree.css("script"):
        normalized = normalize_text(script.text())
        threats.extend(collect_secret_findings(normalized, "script"))
        if any(pattern.search(normalized) for pattern in INJECTION_PATTERNS):
            prompt_injection_detected = True
            threats.append(
                {
                    "type": "script_injection",
                    "snippet": " ".join(normalized.split())[:100],
                }
            )

    scannable_text = normalize_text(tree.text()) + " " + " ".join(hidden_texts)
    for pattern in INJECTION_PATTERNS:
        if pattern.search(scannable_text):
            prompt_injection_detected = True
            threats.append(
                {
                    "type": "prompt_injection_pattern",
                    "pattern": pattern.pattern,
                    "detail": "Adversarial prompt injection pattern detected.",
                }
            )

    return {
        "is_suspicious": len(threats) > 0,
        "prompt_injection_detected": prompt_injection_detected,
        "hidden_elements_count": hidden_count,
        "threats": threats,
    }

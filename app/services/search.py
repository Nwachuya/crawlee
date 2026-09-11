"""Web search for /api/v1/search.

Port of Brainbox `web_tools.py` (search half only) adapted to Crawlee:
- Primary backend: ddgs (DDG JSON API, handles anti-bot/challenge pages).
- Fallback cascade: DDG lite HTML scrape -> Bing HTML -> Google News RSS.
- Network calls use curl_cffi.requests (TLS-impersonating, requests-compatible
  API) instead of requests — no new HTTP client dependency.
- Returns ONLY {title, snippet, url, date} per result, cap 10,
  recency default week.
"""
from __future__ import annotations

import base64
import html as htmlmod
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any

from curl_cffi import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
BING_FRESH = {"day": "ez1", "week": "ez2", "month": "ez3", "year": "ez5", "all": ""}


# ---- Bing helpers ---------------------------------------------------------

def _bing_url(query: str, count: int, freshness: str, region: str) -> str:
    q = urllib.parse.quote_plus(query)
    meta = _region_defaults(region)
    base = (
        f"https://www.bing.com/search?q={q}&count={count}"
        f"&cc={meta['cc']}&setlang={meta['lang']}&setmkt={meta['mkt']}"
    )
    ez = BING_FRESH.get(freshness, "ez2")
    if ez:
        base += f'&filters=ex1%3A%22{ez}%22'
    return base


def _decode_bing_u(u: str) -> str:
    raw = u
    if raw[:2] in ("a1", "a2", "a3"):
        raw = raw[2:]
    padded = raw + "=" * (-len(raw) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode()
    except Exception:
        try:
            return base64.b64decode(padded).decode()
        except Exception:
            return ""


def _parse_bing_html(html: str, count: int) -> list[dict[str, str]]:
    blocks = re.findall(r'<li class="b_algo[^>]*>.*?</li>', html, re.DOTALL)
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for b in blocks:
        if len(out) >= count:
            break
        m_u = re.search(r'href="https://www\.bing\.com/ck/a[^"]*?u=([^&"]+)', b)
        url = ""
        if m_u:
            url = _decode_bing_u(m_u.group(1))
        if not url:
            m2 = re.search(r'<a[^>]*href="(https://[^"]+)"', b)
            if m2:
                url = htmlmod.unescape(m2.group(1))
        if not url or url in seen:
            continue
        if "bing.com" in url or "microsoft.com" in url:
            continue
        seen.add(url)
        m_t = re.search(r'<h2[^>]*>(.*?)</h2>', b, re.DOTALL)
        title = re.sub(r'<[^>]+>', ' ', m_t.group(1)).strip() if m_t else ""
        title = htmlmod.unescape(re.sub(r'\s+', ' ', title)).strip()[:200]
        m_p = re.search(r'<p[^>]*>(.*?)</p>', b, re.DOTALL)
        snippet = re.sub(r'<[^>]+>', ' ', m_p.group(1)).strip() if m_p else ""
        snippet = htmlmod.unescape(re.sub(r'\s+', ' ', snippet)).strip()[:300]
        date = ""
        m_date = re.search(r'(\d{1,2}[\.\s]\w+\s20\d{2})', snippet)
        if m_date:
            date = m_date.group(1).strip()
        out.append({"title": title, "snippet": snippet, "url": url, "date": date})
    return out


# ---- DDG + Google News helpers --------------------------------------------

def _parse_ddg_lite_html(html: str, count: int) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    result_blocks = re.split(r"<a\s+rel=\"nofollow\"\s+href=\"[^\"]*uddg=", html)
    for block in result_blocks[1:]:
        if len(out) >= count:
            break
        url_encoded = re.match(r'([^"&\s]+)', block)
        if not url_encoded:
            continue
        url = urllib.parse.unquote(url_encoded.group(1))
        if url in seen:
            continue
        seen.add(url)

        title_match = re.search(r"class=['\"]result-link['\"]>(.*?)</a>", block, re.DOTALL)
        title = ""
        if title_match:
            title = htmlmod.unescape(re.sub(r'<[^>]+>', '', title_match.group(1)).strip())
            title = re.sub(r'\s+', ' ', title).strip()[:200]

        snippet = ""
        snip_match = re.search(r"class=['\"]result-snippet['\"]>\s*(.*?)\s*</td>", block, re.DOTALL)
        if snip_match:
            snippet = htmlmod.unescape(re.sub(r'<[^>]+>', '', snip_match.group(1)).strip())
            snippet = re.sub(r'\s+', ' ', snippet).strip()[:300]

        date = ""
        ts_match = re.search(r"class=['\"]timestamp['\"]>\s*([\d\-T:.]+)", block)
        if ts_match:
            date = ts_match.group(1).strip()[:30]

        out.append({"title": title, "snippet": snippet, "url": url, "date": date})
    return out


def _parse_google_news_rss(xml_text: str, count: int) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items = root.findall(".//item")
    out: list[dict[str, str]] = []
    for item in items[:count]:
        title_el = item.find("title")
        link_el = item.find("link")
        pub_el = item.find("pubDate")
        desc_el = item.find("description")
        title = (title_el.text or "").strip()[:200] if title_el is not None else ""
        url = (link_el.text or "").strip() if link_el is not None else ""
        desc_raw = (desc_el.text or "") if desc_el is not None else ""
        snippet = re.sub(r'<[^>]+>', ' ', desc_raw)
        snippet = htmlmod.unescape(re.sub(r'\s+', ' ', snippet)).strip()[:300]
        date = (pub_el.text or "").strip() if pub_el is not None else ""
        if url:
            out.append({"title": title, "snippet": snippet, "url": url, "date": date})
    return out


# ---- Result validation ----------------------------------------------------

LOW_VALUE_DOMAINS = {
    "dictionary.com", "merriam-webster.com", "cambridge.org", "thefreedictionary.com",
    "wordreference.com", "vocabulary.com", "britannica.com", "collinsdictionary.com",
    "en.wiktionary.org", "support.google.com", "signup.live.com", "duckduckgo.com",
}
HIJACK_DOMAINS = {
    "thetrainline.com", "nationalrail.co.uk", "amtrak.com", "train.org", "renfe.com",
    "idos.cz", "cd.cz", "irctc.co.in", "bestbuy.com", "bestsecret.com",
}
# Walled-garden social networks only. Reddit/YouTube are content platforms and
# intentionally excluded — they often carry the best answers for tech queries.
SOCIAL_DOMAINS = {
    "facebook.com", "linkedin.com", "instagram.com", "x.com", "twitter.com",
    "tiktok.com", "snapchat.com", "pinterest.com", "threads.net",
}

# Country (lower, 2-letter) -> backend parameters. "ddg" is the DDG region code
# (used by ddgs lib and the lite/kl param); "cc"/"lang"/"mkt" drive Bing; News
# is derived as hl={lang}-{CC}, gl={CC}, ceid={CC}:{lang}. Unknown regions fall
# back to "us".
REGION_META = {
    "us": {"ddg": "us-en", "cc": "US", "lang": "en", "mkt": "en-US"},
    "uk": {"ddg": "uk-en", "cc": "GB", "lang": "en", "mkt": "en-GB"},
    "gb": {"ddg": "uk-en", "cc": "GB", "lang": "en", "mkt": "en-GB"},
    "ie": {"ddg": "ie-en", "cc": "IE", "lang": "en", "mkt": "en-IE"},
    "au": {"ddg": "au-en", "cc": "AU", "lang": "en", "mkt": "en-AU"},
    "ca": {"ddg": "ca-en", "cc": "CA", "lang": "en", "mkt": "en-CA"},
    "nz": {"ddg": "nz-en", "cc": "NZ", "lang": "en", "mkt": "en-NZ"},
    "in": {"ddg": "in-en", "cc": "IN", "lang": "en", "mkt": "en-IN"},
    "za": {"ddg": "za-en", "cc": "ZA", "lang": "en", "mkt": "en-ZA"},
    "sg": {"ddg": "sg-en", "cc": "SG", "lang": "en", "mkt": "en-SG"},
    "ph": {"ddg": "ph-en", "cc": "PH", "lang": "en", "mkt": "en-PH"},
    "pk": {"ddg": "pk-en", "cc": "PK", "lang": "en", "mkt": "en-PK"},
    "my": {"ddg": "my-ms", "cc": "MY", "lang": "ms", "mkt": "ms-MY"},
    "de": {"ddg": "de-de", "cc": "DE", "lang": "de", "mkt": "de-DE"},
    "at": {"ddg": "at-de", "cc": "AT", "lang": "de", "mkt": "de-AT"},
    "ch": {"ddg": "ch-de", "cc": "CH", "lang": "de", "mkt": "de-CH"},
    "fr": {"ddg": "fr-fr", "cc": "FR", "lang": "fr", "mkt": "fr-FR"},
    "be": {"ddg": "be-fr", "cc": "BE", "lang": "fr", "mkt": "fr-BE"},
    "es": {"ddg": "es-es", "cc": "ES", "lang": "es", "mkt": "es-ES"},
    "mx": {"ddg": "mx-es", "cc": "MX", "lang": "es", "mkt": "es-MX"},
    "ar": {"ddg": "ar-es", "cc": "AR", "lang": "es", "mkt": "es-AR"},
    "cl": {"ddg": "cl-es", "cc": "CL", "lang": "es", "mkt": "es-CL"},
    "co": {"ddg": "co-es", "cc": "CO", "lang": "es", "mkt": "es-CO"},
    "pe": {"ddg": "pe-es", "cc": "PE", "lang": "es", "mkt": "es-PE"},
    "it": {"ddg": "it-it", "cc": "IT", "lang": "it", "mkt": "it-IT"},
    "nl": {"ddg": "nl-nl", "cc": "NL", "lang": "nl", "mkt": "nl-NL"},
    "pt": {"ddg": "pt-pt", "cc": "PT", "lang": "pt", "mkt": "pt-PT"},
    "br": {"ddg": "br-pt", "cc": "BR", "lang": "pt", "mkt": "pt-BR"},
    "ru": {"ddg": "ru-ru", "cc": "RU", "lang": "ru", "mkt": "ru-RU"},
    "ua": {"ddg": "ua-uk", "cc": "UA", "lang": "uk", "mkt": "uk-UA"},
    "pl": {"ddg": "pl-pl", "cc": "PL", "lang": "pl", "mkt": "pl-PL"},
    "se": {"ddg": "se-sv", "cc": "SE", "lang": "sv", "mkt": "sv-SE"},
    "no": {"ddg": "no-no", "cc": "NO", "lang": "no", "mkt": "nb-NO"},
    "dk": {"ddg": "dk-da", "cc": "DK", "lang": "da", "mkt": "da-DK"},
    "fi": {"ddg": "fi-fi", "cc": "FI", "lang": "fi", "mkt": "fi-FI"},
    "cz": {"ddg": "cz-cs", "cc": "CZ", "lang": "cs", "mkt": "cs-CZ"},
    "sk": {"ddg": "sk-sk", "cc": "SK", "lang": "sk", "mkt": "sk-SK"},
    "hu": {"ddg": "hu-hu", "cc": "HU", "lang": "hu", "mkt": "hu-HU"},
    "ro": {"ddg": "ro-ro", "cc": "RO", "lang": "ro", "mkt": "ro-RO"},
    "gr": {"ddg": "gr-el", "cc": "GR", "lang": "el", "mkt": "el-GR"},
    "tr": {"ddg": "tr-tr", "cc": "TR", "lang": "tr", "mkt": "tr-TR"},
    "jp": {"ddg": "jp-jp", "cc": "JP", "lang": "ja", "mkt": "ja-JP"},
    "kr": {"ddg": "kr-kr", "cc": "KR", "lang": "ko", "mkt": "ko-KR"},
    "cn": {"ddg": "cn-zh", "cc": "CN", "lang": "zh", "mkt": "zh-CN"},
    "tw": {"ddg": "tw-tzh", "cc": "TW", "lang": "zh", "mkt": "zh-TW"},
    "hk": {"ddg": "hk-tzh", "cc": "HK", "lang": "zh", "mkt": "zh-HK"},
    "th": {"ddg": "th-th", "cc": "TH", "lang": "th", "mkt": "th-TH"},
    "vn": {"ddg": "vn-vn", "cc": "VN", "lang": "vi", "mkt": "vi-VN"},
    "id": {"ddg": "id-id", "cc": "ID", "lang": "id", "mkt": "id-ID"},
    "il": {"ddg": "il-he", "cc": "IL", "lang": "he", "mkt": "he-IL"},
    "sa": {"ddg": "sa-ar", "cc": "SA", "lang": "ar", "mkt": "ar-SA"},
    "ae": {"ddg": "ae-en", "cc": "AE", "lang": "en", "mkt": "en-AE"},
    "eg": {"ddg": "eg-ar", "cc": "EG", "lang": "ar", "mkt": "ar-EG"},
}

DEFAULT_REGION = "us"


def _region_defaults(region: str) -> dict[str, str]:
    code = (region or "").strip().lower()
    meta = REGION_META.get(code) or REGION_META[DEFAULT_REGION]
    return {
        "ddg": meta["ddg"],
        "cc": meta["cc"],
        "lang": meta["lang"],
        "mkt": meta["mkt"],
        "hl": f"{meta['lang']}-{meta['cc']}",
    }


def _is_social_domain(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in SOCIAL_DOMAINS)


def _clean_search_results(
    results: list[dict[str, str]],
    query: str,
    exclude_social: bool = False,
) -> list[dict[str, str]]:
    if not results:
        return []
    q_words = set(re.findall(r"[a-z0-9]+", query.lower()))

    out: list[dict[str, str]] = []
    for r in results:
        url = (r.get("url") or "").lower()
        title = (r.get("title") or "").lower()
        snippet = (r.get("snippet") or "").lower()
        try:
            host = urllib.parse.urlparse(url).hostname or ""
        except Exception:
            host = ""
        if host.startswith("www."):
            host = host[4:]
        if exclude_social and _is_social_domain(host):
            continue
        if any(h in url for h in HIJACK_DOMAINS):
            continue
        low_val = any(host == d or host.endswith("." + d) for d in LOW_VALUE_DOMAINS)
        if low_val and "definition" not in q_words and "define" not in q_words:
            continue
        if q_words:
            hay = title + " " + snippet + " " + url
            hits = [w for w in q_words if w in hay and len(w) > 2]
            if not hits:
                continue
        out.append(r)
        if len(out) >= 10:
            break
    return out


# ---- Public API -----------------------------------------------------------

def _merge_dedup(results: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for r in results:
        url = (r.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(r)
    return out


def _search_ddgs(query: str, count: int, freshness: str, region: str) -> list[dict[str, str]]:
    """DuckDuckGo via the ddgs library — handles anti-bot/challenge pages.

    DDG's timelimit (recency) filter is flaky under rate limiting: it can
    return sparse results. Retry the filtered attempt once, then pad with an
    unfiltered attempt so callers always get a useful set.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return []
    timelimit_map = {"day": "d", "week": "w", "month": "m", "year": "y"}
    timelimit = timelimit_map.get(freshness) if freshness != "all" else None
    ddg_region = _region_defaults(region)["ddg"]

    def _run(ddgs, tl) -> list[dict[str, str]]:
        raw = ddgs.text(
            query,
            max_results=count,
            region=ddg_region,
            backend="auto",
            timelimit=tl,
        )
        return [
            {
                "title": (r.get("title") or "").strip()[:200],
                "snippet": (r.get("body") or "").strip()[:300],
                "url": (r.get("href") or "").strip(),
                "date": (r.get("date") or "").strip(),
            }
            for r in (raw or [])
            if r.get("href")
        ]

    try:
        with DDGS(timeout=12) as ddgs:
            first = _run(ddgs, timelimit)
            if len(first) < min(count, 5):
                time.sleep(1.5)
                second = _run(ddgs, timelimit)
            else:
                second = []
            results = _merge_dedup(first + second)
            if len(results) < min(count, 3) and timelimit:
                time.sleep(1.5)
                results = _merge_dedup(results + _run(ddgs, None))
            return results
    except Exception:
        return []


def web_search(
    query: str,
    count: int = 10,
    freshness: str = "week",
    region: str = "us",
    exclude_social: bool = False,
) -> dict[str, Any]:
    query = (query or "").strip()
    if not query or len(query) < 2:
        raise ValueError("query is required (min 2 chars)")
    if len(query) > 200:
        raise ValueError("query too long (max 200 chars)")
    count = max(1, min(10, int(count or 10)))
    freshness = (freshness or "week").strip().lower()
    if freshness not in BING_FRESH:
        freshness = "week"
    region = (region or "").strip().lower()

    # 1) ddgs — robust DDG search, handles anti-bot + returns title/snippet/url/date
    try:
        parsed = _search_ddgs(query, count, freshness, region)
        if parsed:
            cleaned = _clean_search_results(parsed, query, exclude_social)
            if cleaned:
                return {"results": cleaned[:count]}
    except Exception:
        pass

    # 2) DDG lite HTML scrape — fallback when ddgs unavailable
    try:
        ddg_params = {"q": query}
        df_map = {"day": "d", "week": "w", "month": "m", "year": "y"}
        if freshness in df_map:
            ddg_params["df"] = df_map[freshness]
        ddg_params["kl"] = _region_defaults(region)["ddg"]
        r = requests.post("https://lite.duckduckgo.com/lite/", data=ddg_params,
                          headers={"User-Agent": UA, "Accept": "text/html", "Accept-Language": "en-US,en;q=0.9"},
                          timeout=10)
        if r.ok and r.text:
            parsed = _parse_ddg_lite_html(r.text, count)
            if parsed:
                cleaned = _clean_search_results(parsed, query, exclude_social)
                if cleaned:
                    return {"results": cleaned[:count]}
    except Exception:
        pass

    # 3) Bing dated supplement — use when freshness != all and DDG missed
    try:
        headers_bing = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
        url = _bing_url(query, count, freshness, region)
        r = requests.get(url, headers=headers_bing, timeout=10)
        if r.ok and r.text:
            parsed = _parse_bing_html(r.text, count)
            if parsed:
                cleaned = _clean_search_results(parsed, query, exclude_social)
                if cleaned:
                    return {"results": cleaned[:count]}
            url2 = _bing_url(query, count, "all", region)
            r2 = requests.get(url2, headers=headers_bing, timeout=10)
            if r2.ok and r2.text:
                parsed2 = _parse_bing_html(r2.text, count)
                if parsed2:
                    cleaned2 = _clean_search_results(parsed2, query, exclude_social)
                    if cleaned2:
                        return {"results": cleaned2[:count]}
    except Exception:
        pass

    # 4) Google News RSS (web news supplement, when:7d etc)
    try:
        when_map = {"day": "1d", "week": "7d", "month": "30d", "year": "12m"}
        when = when_map.get(freshness, "7d") if freshness != "all" else ""
        q = f"{query} when:{when}" if when else query
        meta = _region_defaults(region)
        rss_url = (
            f"https://news.google.com/rss/search?q={urllib.parse.quote_plus(q)}"
            f"&hl={meta['hl']}&gl={meta['cc']}&ceid={meta['cc']}:{meta['lang']}"
        )
        r = requests.get(rss_url, headers={"User-Agent": UA, "Accept": "application/rss+xml,application/xml"}, timeout=10)
        if r.ok and r.text:
            parsed = _parse_google_news_rss(r.text, count)
            if parsed:
                cleaned = _clean_search_results(parsed, query, exclude_social)
                if cleaned:
                    return {"results": cleaned[:count]}
    except Exception:
        pass

    return {"results": []}
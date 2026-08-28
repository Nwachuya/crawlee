from fastapi import HTTPException
from fastapi.testclient import TestClient
from selectolax.parser import HTMLParser

import main
from main import (
    app,
    build_export_formats,
    classify_complexity,
    extract_sections_from_markdown,
    generate_question,
    scan_security_threats,
)


def test_build_export_formats_uses_context_quote_for_alpaca():
    export = build_export_formats(
        question="What is Crawlee?",
        ideal_answer="A scraping tool.",
        context_quote="Context from the source page.",
        system_prompt="You are a helpful assistant.",
    )

    assert export["alpaca"]["input"] == "Context from the source page."


def test_classify_complexity_marks_code_heavy_text_as_intermediate():
    result = classify_complexity("The API returns JSON over HTTP.")

    assert result == "intermediate"


def test_generate_question_for_procedural_heading():
    result = generate_question("API Quickstart")

    assert result["type"] == "procedural"
    assert "API Quickstart" in result["question"]


def test_scrape_handles_img_alt_attribute_without_value(monkeypatch):
    async def fake_fetch_html(target_url: str, impersonate: str) -> str:
        return "<html><body><img src='/image.png' alt><p>Hello world content block for extraction.</p></body></html>"

    monkeypatch.setattr(main, "fetch_html", fake_fetch_html)
    client = TestClient(app)

    response = client.post("/scrape", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["media"]["images"][0]["alt"] == ""


def test_scrape_rejects_non_progressing_chunk_settings():
    client = TestClient(app)

    response = client.post(
        "/scrape",
        json={"url": "https://stripe.com/docs", "chunk_size": 100, "chunk_overlap": 100},
    )

    assert response.status_code == 422
    assert "chunk_overlap must be smaller than chunk_size" in response.text


def test_scrape_preserves_upstream_http_status(monkeypatch):
    async def fake_fetch_html(target_url: str, impersonate: str) -> str:
        raise HTTPException(status_code=404, detail="Failed to fetch target URL")

    monkeypatch.setattr(main, "fetch_html", fake_fetch_html)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/scrape", json={"url": "https://docs.github.com/en"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Failed to fetch target URL"


def test_security_audit_ignores_short_aria_hidden_ui_noise():
    tree = HTMLParser('<html><body><span aria-hidden="true">•</span></body></html>')

    result = scan_security_threats(tree, tree.html)

    assert result["is_suspicious"] is False
    assert result["threats"] == []


def test_security_audit_ignores_non_injection_aria_hidden_copy():
    tree = HTMLParser(
        '<html><body><span aria-hidden="true">Select language: current language is English</span></body></html>'
    )

    result = scan_security_threats(tree, tree.html)

    assert result["is_suspicious"] is False
    assert result["threats"] == []


def test_extract_sections_from_markdown_collects_heading_bodies():
    sections = extract_sections_from_markdown(
        "# Intro\nThis section has enough content to be captured for dataset generation.\n\n## API\nUse the API with a secret key and send JSON requests.\n"
    )

    assert [section["heading"] for section in sections] == ["Intro", "API"]


def test_extract_sections_from_markdown_falls_back_to_paragraphs():
    sections = extract_sections_from_markdown(
        "Cloudflare is a connectivity platform for businesses with enough prose to create a dataset entry.\n\n"
        "It also provides security and performance tooling for Internet properties at scale."
    )

    assert [section["heading"] for section in sections] == ["Section 1", "Section 2"]


def test_dataset_falls_back_to_markdown_sections(monkeypatch):
    async def fake_fetch_html(target_url: str, impersonate: str) -> str:
        return "<html><head><title>Docs</title></head><body><div>No headings here</div></body></html>"

    def fake_extract(*args, **kwargs):
        return "# Billing\nBilling setup instructions with enough detail to generate a question and answer pair."

    monkeypatch.setattr(main, "fetch_html", fake_fetch_html)
    monkeypatch.setattr(main.trafilatura, "extract", fake_extract)
    client = TestClient(app)

    response = client.post("/dataset", json={"url": "https://developers.cloudflare.com/fundamentals/"})

    assert response.status_code == 200
    assert response.json()["total_pairs_generated"] == 1

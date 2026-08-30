from fastapi import APIRouter

from ..schemas import ScrapeRequest
from ..services.fetch import fetch_page
from ..services.scrape import build_scrape_response


router = APIRouter()


@router.post("/scrape")
async def scrape_endpoint(payload: ScrapeRequest):
    page = await fetch_page(str(payload.url), payload.impersonate)
    return build_scrape_response(
        target_url=page["url"],
        html_text=page["html"],
        headers=page["headers"],
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        selectors=payload.selectors,
        fit_markdown=bool(payload.fit_markdown),
        sanitize_injections=bool(payload.sanitize_injections),
    )

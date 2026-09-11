from fastapi import APIRouter

from ..schemas import SearchRequest
from ..services.search import web_search


router = APIRouter()


@router.post("/search")
def search_endpoint(payload: SearchRequest) -> dict:
    query = payload.query.strip()
    results = web_search(
        query=query,
        count=payload.count,
        freshness=payload.freshness,
        region=payload.region,
        exclude_social=payload.exclude_social,
    )
    return {
        "success": True,
        "query": query,
        "results": results["results"],
    }
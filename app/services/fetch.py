from fastapi import HTTPException
from curl_cffi.requests import AsyncSession


async def fetch_page(target_url: str, impersonate: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    async with AsyncSession(impersonate=impersonate) as session:
        try:
            response = await session.get(target_url, headers=headers, timeout=15)
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch target URL")
            return {
                "url": str(response.url),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "html": response.text,
            }
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Fetch error: {str(exc)}") from exc


async def fetch_html(target_url: str, impersonate: str) -> str:
    return (await fetch_page(target_url, impersonate))["html"]

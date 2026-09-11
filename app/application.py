import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .routes.dataset import router as dataset_router
from .routes.health import router as health_router
from .routes.home import router as home_router
from .routes.scrape import router as scrape_router
from .routes.search import router as search_router
from .routes.security_audit import router as security_audit_router

app = FastAPI(
    title="AI-Native Ultra-Light Scraper & Dataset Engine",
    version="3.0.0",
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path in ("/", "/api/v1/health"):
        return await call_next(request)

    api_key = os.environ.get("X_API_KEY", "")
    if not api_key:
        return await call_next(request)

    provided = request.headers.get("X-Api-Key", "")
    if not provided:
        return JSONResponse(status_code=401, content={"detail": "Missing X-Api-Key header"})
    if provided != api_key:
        return JSONResponse(status_code=403, content={"detail": "Invalid API key"})

    return await call_next(request)


app.include_router(home_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(scrape_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(security_audit_router, prefix="/api/v1")
app.include_router(dataset_router, prefix="/api/v1")

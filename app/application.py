from fastapi import FastAPI

from .routes.dataset import router as dataset_router
from .routes.health import router as health_router
from .routes.scrape import router as scrape_router
from .routes.security_audit import router as security_audit_router


app = FastAPI(
    title="AI-Native Ultra-Light Scraper & Dataset Engine",
    version="3.0.0",
)

app.include_router(health_router)
app.include_router(scrape_router)
app.include_router(security_audit_router)
app.include_router(dataset_router)

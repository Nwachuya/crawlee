from fastapi import APIRouter
from selectolax.parser import HTMLParser

from ..schemas import AuditRequest
from ..services.fetch import fetch_html
from ..services.security import scan_security_threats


router = APIRouter()


@router.post("/security-audit")
async def security_audit_endpoint(payload: AuditRequest):
    target_url = str(payload.url)
    html_text = await fetch_html(target_url, payload.impersonate)
    tree = HTMLParser(html_text)
    return {
        "success": True,
        "url": target_url,
        "security_audit": scan_security_threats(tree, html_text),
    }

from typing import Dict, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator


class BaseRequest(BaseModel):
    url: HttpUrl
    impersonate: Optional[str] = "chrome120"


class ScrapeRequest(BaseRequest):
    chunk_size: int = Field(default=0, ge=0)
    chunk_overlap: int = Field(default=100, ge=0)
    selectors: Optional[Dict[str, str]] = None
    fit_markdown: Optional[bool] = False
    sanitize_injections: Optional[bool] = True

    @model_validator(mode="after")
    def validate_chunk_settings(self) -> "ScrapeRequest":
        if self.chunk_size > 0 and self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size when chunking is enabled")
        return self


class AuditRequest(BaseRequest):
    pass


class DatasetRequest(BaseRequest):
    min_confidence: Optional[float] = 0.80

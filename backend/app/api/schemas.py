from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScanCreateRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class ProviderResultResponse(BaseModel):
    provider: str
    status: str
    verdict: str
    observed_at: datetime
    details: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None


class ScanResponse(BaseModel):
    id: UUID
    url: str
    status: str
    overall_verdict: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any] | None
    providers: list[ProviderResultResponse]
    deduplicated: bool = False

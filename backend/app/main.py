from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.url_policy import URLPolicyError, validate_submitted_url

app = FastAPI(
    title="URL Security Scanner API",
    version="0.1.0",
    description="Defensive URL reputation API scaffold; live scans are not enabled.",
)


class ScanRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


@app.get("/healthz", tags=["operations"])
def health() -> dict[str, str]:
    """Process health only; this says nothing about a URL's safety."""
    return {"status": "ok", "scan_execution": "disabled"}


@app.post("/api/v1/scans", status_code=501, tags=["scans"])
def create_scan(request: ScanRequest) -> None:
    """Validate accepted syntax but never invent or simulate a scan result."""
    try:
        validate_submitted_url(request.url)
    except URLPolicyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    raise HTTPException(
        status_code=501,
        detail=(
            "Live scanning is not configured. No provider was called and no security "
            "verdict was produced."
        ),
    )

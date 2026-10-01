from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.url_policy import URLPolicyError, validate_submitted_url

app = FastAPI(
    title="bağlantı güvenlik kontrolü api'si",
    version="0.1.0",
    description="savunma amaçlı bağlantı itibarı api'si; canlı tarama henüz açık değil.",
)


class ScanRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


@app.get("/healthz", tags=["işletim"])
def health() -> dict[str, str]:
    """yalnızca api sürecinin çalıştığını bildirir; bağlantı güvenliğini ölçmez."""
    return {"status": "ok", "scan_execution": "disabled"}


@app.post("/api/v1/scans", status_code=501, tags=["tarama"])
def create_scan(request: ScanRequest) -> None:
    """adres biçimini kontrol eder ama tarama sonucu uydurmaz veya taklit etmez."""
    try:
        validate_submitted_url(request.url)
    except URLPolicyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    raise HTTPException(
        status_code=501,
        detail="canlı tarama henüz hazır değil. hiçbir güvenlik servisi çağrılmadı, sonuç üretilmedi.",
    )

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.api.schemas import ProviderResultResponse, ScanCreateRequest, ScanResponse
from app.core.config import get_settings
from app.core.runtime import enforce_scan_rate_limit, get_redis
from app.db import engine, get_db
from app.models import Scan, ScanStatus
from app.providers.base import Verdict
from app.services.scans import QueueFullError, QueueUnavailableError, enqueue_scan
from app.services.url_policy import URLPolicyError

app = FastAPI(
    title="bağlantı güvenlik kontrolü api'si",
    version="0.2.0",
    description="gerçek itibar servisleri ve güvenli bağlantı gözlemi kullanan savunma amaçlı tarama api'si.",
)

DbSession = Annotated[Session, Depends(get_db)]
RedisConnection = Annotated[Redis, Depends(get_redis)]


def _overall_verdict(scan: Scan) -> str:
    completed = [item for item in scan.provider_results if item.status == "completed"]
    if any(item.verdict == Verdict.MALICIOUS.value for item in completed):
        return Verdict.MALICIOUS.value
    if any(item.verdict == Verdict.SUSPICIOUS.value for item in completed):
        return Verdict.SUSPICIOUS.value
    if any(item.verdict == Verdict.CLEAN.value for item in completed):
        return Verdict.CLEAN.value
    return Verdict.UNKNOWN.value


def _scan_response(scan: Scan, deduplicated: bool = False) -> ScanResponse:
    metadata = scan.metadata_record.data if scan.metadata_record else None
    providers = [
        ProviderResultResponse(
            provider=item.provider,
            status=item.status,
            verdict=item.verdict,
            observed_at=item.observed_at,
            details=item.details,
            error_code=item.error_code,
            error_message=item.error_message,
        )
        for item in sorted(scan.provider_results, key=lambda result: result.provider)
    ]
    return ScanResponse(
        id=scan.id,
        url=scan.target.canonical_url,
        status=scan.status,
        overall_verdict=_overall_verdict(scan),
        created_at=scan.created_at,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_code=scan.error_code,
        error_message=scan.error_message,
        metadata=metadata,
        providers=providers,
        deduplicated=deduplicated,
    )


def _get_scan(db: Session, scan_id: UUID) -> Scan | None:
    return db.scalar(
        select(Scan)
        .options(
            selectinload(Scan.target),
            selectinload(Scan.metadata_record),
            selectinload(Scan.provider_results),
        )
        .where(Scan.id == scan_id)
    )


@app.get("/healthz", tags=["işletim"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health", tags=["işletim"])
def readiness(redis: RedisConnection) -> JSONResponse:
    checks = {"database": "ok", "redis": "ok"}
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except SQLAlchemyError:
        checks["database"] = "unavailable"
    try:
        redis.ping()
    except RedisError:
        checks["redis"] = "unavailable"
    ready = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ok" if ready else "degraded", "checks": checks},
    )


@app.post("/api/scans", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED, tags=["scans"])
def create_scan(
    body: ScanCreateRequest,
    request: Request,
    response: Response,
    db: DbSession,
    redis: RedisConnection,
) -> ScanResponse:
    enforce_scan_rate_limit(request, redis)
    try:
        scan, deduplicated = enqueue_scan(db, redis, body.url)
    except URLPolicyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except QueueFullError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except QueueUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    scan = _get_scan(db, scan.id)
    if scan is None:
        raise HTTPException(status_code=500, detail="oluşturulan tarama kaydı okunamadı.")
    response.headers["Location"] = f"/api/scans/{scan.id}"
    return _scan_response(scan, deduplicated)


@app.get("/api/scans/{scan_id}", response_model=ScanResponse, tags=["scans"])
def get_scan(scan_id: UUID, db: DbSession) -> ScanResponse:
    scan = _get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="tarama kaydı bulunamadı.")
    if scan.status in {ScanStatus.QUEUED.value, ScanStatus.RUNNING.value}:
        start = scan.started_at or scan.created_at
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        if datetime.now(UTC) - start > timedelta(seconds=get_settings().scan_job_timeout_seconds * 2):
            scan.status = ScanStatus.FAILED.value
            scan.completed_at = datetime.now(UTC)
            scan.error_code = "worker_timeout"
            scan.error_message = "tarama zaman sınırını aştı; yeniden deneyebilirsin."
            db.commit()
            scan = _get_scan(db, scan_id) or scan
    return _scan_response(scan)


@app.get("/api/scans/{scan_id}/results", tags=["scans"])
def get_scan_results(scan_id: UUID, db: DbSession) -> dict[str, object]:
    scan = _get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="tarama kaydı bulunamadı.")
    result = _scan_response(scan)
    return {
        "scan_id": str(scan.id),
        "status": scan.status,
        "overall_verdict": result.overall_verdict,
        "metadata": result.metadata,
        "providers": [item.model_dump(mode="json") for item in result.providers],
    }

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from app.db import SessionLocal
from app.models import ProviderResult, Scan, ScanMetadata, ScanStatus
from app.providers.base import ProviderOutcome, Verdict
from app.providers.registry import run_providers
from app.services.metadata import inspect_url
from app.services.url_policy import UnsafeTargetError


def overall_verdict(outcomes: list[ProviderOutcome]) -> str:
    real = [item for item in outcomes if item.status.value == "completed"]
    if any(item.verdict == Verdict.MALICIOUS for item in real):
        return Verdict.MALICIOUS.value
    if any(item.verdict == Verdict.SUSPICIOUS for item in real):
        return Verdict.SUSPICIOUS.value
    if any(item.verdict == Verdict.CLEAN for item in real):
        return Verdict.CLEAN.value
    return Verdict.UNKNOWN.value


def process_scan(scan_id: str) -> None:
    """rq işi: hedefi güvenle gözlemler, ayarlı provider'ları çağırır ve sonucu saklar."""
    db = SessionLocal()
    try:
        scan = db.scalar(select(Scan).where(Scan.id == UUID(scan_id)))
        if scan is None or scan.status != ScanStatus.QUEUED.value:
            return
        scan.status = ScanStatus.RUNNING.value
        scan.started_at = datetime.now(UTC)
        db.commit()

        target_url = scan.submitted_url
        try:
            metadata = asyncio.run(inspect_url(target_url))
        except UnsafeTargetError as exc:
            db.add(ScanMetadata(scan_id=scan.id, status="blocked", data={"reason": str(exc)}))
            scan.status = ScanStatus.FAILED.value
            scan.error_code = "unsafe_dns_or_redirect"
            scan.error_message = str(exc)[:500]
            scan.completed_at = datetime.now(UTC)
            db.commit()
            return
        db.add(ScanMetadata(scan_id=scan.id, status=metadata.get("status", "unknown"), data=metadata))
        db.commit()

        if metadata.get("status") == "redirect_blocked":
            scan.status = ScanStatus.FAILED.value
            scan.error_code = "unsafe_redirect"
            scan.error_message = "güvenli olmayan yönlendirme algılandı; istek burada durduruldu."
            scan.completed_at = datetime.now(UTC)
            db.commit()
            return

        outcomes = asyncio.run(run_providers(target_url))
        for outcome in outcomes:
            db.add(ProviderResult(
                scan_id=scan.id,
                provider=outcome.provider,
                status=outcome.status.value,
                verdict=outcome.verdict.value,
                details=outcome.details,
                error_code=outcome.error_code,
                error_message=outcome.error_message,
            ))
        scan.status = ScanStatus.COMPLETED.value
        scan.completed_at = datetime.now(UTC)
        db.commit()
    except Exception:  # noqa: BLE001 - persist a failed scan for unexpected job errors
        db.rollback()
        scan = db.scalar(select(Scan).where(Scan.id == UUID(scan_id)))
        if scan is not None:
            scan.status = ScanStatus.FAILED.value
            scan.completed_at = datetime.now(UTC)
            scan.error_code = "worker_error"
            scan.error_message = "tarama işlenirken beklenmeyen bir hata oluştu."
            db.commit()
    finally:
        db.close()

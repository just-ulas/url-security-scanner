
from sqlalchemy import select

from app.models import ProviderResult, Scan, ScanStatus, Target
from app.providers.base import ProviderOutcome, ProviderStatus, Verdict
from app.services.url_policy import UnsafeTargetError, normalize_url
from app.worker import tasks


def create_queued_scan(factory):
    normalized = normalize_url("https://example.com/")
    with factory() as db:
        target = Target(
            canonical_url=normalized.url,
            canonical_hash=normalized.fingerprint,
            hostname=normalized.hostname,
            scheme=normalized.scheme,
            port=normalized.port,
        )
        db.add(target)
        db.flush()
        scan = Scan(target_id=target.id, submitted_url=normalized.url, status=ScanStatus.QUEUED.value)
        db.add(scan)
        db.commit()
        return str(scan.id)


def test_worker_completes_scan_and_persists_real_provider_outcome(test_session_factory, monkeypatch):
    scan_id = create_queued_scan(test_session_factory)
    monkeypatch.setattr(tasks, "SessionLocal", test_session_factory)

    async def metadata(url):
        return {"status": "observed", "http": {"status": 200}}

    async def providers(url):
        return [ProviderOutcome("test_provider", ProviderStatus.COMPLETED, Verdict.SUSPICIOUS, {"evidence": "fixture"})]

    monkeypatch.setattr(tasks, "inspect_url", metadata)
    monkeypatch.setattr(tasks, "run_providers", providers)
    tasks.process_scan(scan_id)

    with test_session_factory() as db:
        scan = db.scalar(select(Scan).where(Scan.id == __import__("uuid").UUID(scan_id)))
        result = db.scalar(select(ProviderResult).where(ProviderResult.scan_id == scan.id))
        assert scan.status == ScanStatus.COMPLETED.value
        assert result.verdict == Verdict.SUSPICIOUS.value
        assert result.details == {"evidence": "fixture"}


def test_worker_blocks_private_dns_before_provider_calls(test_session_factory, monkeypatch):
    scan_id = create_queued_scan(test_session_factory)
    monkeypatch.setattr(tasks, "SessionLocal", test_session_factory)
    called = False

    async def blocked(url):
        raise UnsafeTargetError("yerel ip engellendi")

    async def providers(url):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(tasks, "inspect_url", blocked)
    monkeypatch.setattr(tasks, "run_providers", providers)
    tasks.process_scan(scan_id)

    with test_session_factory() as db:
        scan = db.scalar(select(Scan).where(Scan.id == __import__("uuid").UUID(scan_id)))
        assert scan.status == ScanStatus.FAILED.value
        assert scan.error_code == "unsafe_dns_or_redirect"
        assert called is False

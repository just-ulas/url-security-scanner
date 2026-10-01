from datetime import UTC, datetime
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError
from rq import Queue
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Scan, ScanStatus, Target
from app.services.url_policy import normalize_url

QUEUE_NAME = "url-scans"


class QueueUnavailableError(RuntimeError):
    pass


class QueueFullError(RuntimeError):
    pass


def enqueue_scan(db: Session, redis: Redis, submitted_url: str) -> tuple[Scan, bool]:
    settings = get_settings()
    normalized = normalize_url(submitted_url)
    try:
        target = db.scalar(select(Target).where(Target.canonical_hash == normalized.fingerprint))
        if target is None:
            target = Target(
                canonical_url=normalized.url,
                canonical_hash=normalized.fingerprint,
                hostname=normalized.hostname,
                scheme=normalized.scheme,
                port=normalized.port,
            )
            db.add(target)
            db.flush()
        active = db.scalar(
            select(Scan)
            .where(Scan.target_id == target.id, Scan.status.in_([ScanStatus.QUEUED.value, ScanStatus.RUNNING.value]))
            .order_by(Scan.created_at.desc())
        )
        if active is not None:
            return active, True
        try:
            queue = Queue(QUEUE_NAME, connection=redis, default_timeout=settings.scan_job_timeout_seconds)
            if queue.count >= settings.scan_queue_limit:
                raise QueueFullError("tarama kuyruğu şu anda dolu. biraz sonra yeniden dene.")
        except RedisError as exc:
            raise QueueUnavailableError("tarama kuyruğuna şu an ulaşılamıyor.") from exc
        scan = Scan(target_id=target.id, submitted_url=normalized.url, status=ScanStatus.QUEUED.value)
        db.add(scan)
        db.commit()
        db.refresh(scan)
    except IntegrityError:
        db.rollback()
        target = db.scalar(select(Target).where(Target.canonical_hash == normalized.fingerprint))
        active = db.scalar(
            select(Scan)
            .where(Scan.target_id == target.id, Scan.status.in_([ScanStatus.QUEUED.value, ScanStatus.RUNNING.value]))
            .order_by(Scan.created_at.desc())
        ) if target else None
        if active:
            return active, True
        raise
    except (QueueFullError, QueueUnavailableError):
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    try:
        from app.worker.tasks import process_scan

        queue.enqueue(
            process_scan,
            str(scan.id),
            job_timeout=settings.scan_job_timeout_seconds,
            result_ttl=0,
            failure_ttl=86400,
        )
    except Exception as exc:
        scan.status = ScanStatus.FAILED.value
        scan.completed_at = datetime.now(UTC)
        scan.error_code = "queue_unavailable"
        scan.error_message = "tarama işi kuyruğa eklenemedi; yeniden deneyebilirsin."
        db.commit()
        raise QueueUnavailableError("tarama işi kuyruğa eklenemedi.") from exc
    return scan, False


def load_scan(db: Session, scan_id: UUID) -> Scan | None:
    return db.scalar(select(Scan).where(Scan.id == scan_id))

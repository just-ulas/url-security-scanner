from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ScanStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Verdict(StrEnum):
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    CLEAN = "clean"
    UNKNOWN = "unknown"


def utcnow() -> datetime:
    return datetime.now(UTC)


json_type = JSON().with_variant(JSONB, "postgresql")


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    hostname: Mapped[str] = mapped_column(String(253), nullable=False, index=True)
    scheme: Mapped[str] = mapped_column(String(8), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    scans: Mapped[list["Scan"]] = relationship(back_populates="target")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    target_id: Mapped[UUID] = mapped_column(ForeignKey("targets.id", ondelete="CASCADE"), nullable=False)
    submitted_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default=ScanStatus.QUEUED.value, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(500))
    target: Mapped[Target] = relationship(back_populates="scans")
    metadata_record: Mapped["ScanMetadata | None"] = relationship(
        back_populates="scan", uselist=False, cascade="all, delete-orphan"
    )
    provider_results: Mapped[list["ProviderResult"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )


Index(
    "uq_scans_active_target",
    Scan.target_id,
    unique=True,
    postgresql_where=text("status IN ('queued', 'running')"),
    sqlite_where=text("status IN ('queued', 'running')"),
)


class ScanMetadata(Base):
    __tablename__ = "scan_metadata"

    scan_id: Mapped[UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    data: Mapped[dict] = mapped_column(json_type, nullable=False, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    scan: Mapped[Scan] = relationship(back_populates="metadata_record")


class ProviderResult(Base):
    __tablename__ = "provider_results"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    scan_id: Mapped[UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), default=Verdict.UNKNOWN.value, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    details: Mapped[dict] = mapped_column(json_type, nullable=False, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(String(500))
    scan: Mapped[Scan] = relationship(back_populates="provider_results")
    __table_args__ = (UniqueConstraint("scan_id", "provider", name="uq_scan_provider"),)

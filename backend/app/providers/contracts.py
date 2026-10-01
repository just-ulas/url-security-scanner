"""ileride eklenecek gerçek güvenlik servisleri için ortak yanıt biçimi."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class Verdict(StrEnum):
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    CLEAN = "clean"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass(frozen=True)
class ProviderObservation:
    provider: str
    verdict: Verdict
    observed_at: datetime
    reference: str | None = None
    explanation: str | None = None


class ReputationProvider(Protocol):
    name: str

    async def lookup(self, url: str) -> ProviderObservation: ...

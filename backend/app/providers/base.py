from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class ProviderStatus(StrEnum):
    NOT_CONFIGURED = "not_configured"
    COMPLETED = "completed"
    NO_DATA = "no_data"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class Verdict(StrEnum):
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    CLEAN = "clean"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderOutcome:
    provider: str
    status: ProviderStatus
    verdict: Verdict = Verdict.UNKNOWN
    details: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


class ReputationProvider(Protocol):
    name: str

    async def lookup(self, url: str) -> ProviderOutcome: ...


def http_error_outcome(provider: str, status_code: int) -> ProviderOutcome:
    if status_code == 429:
        return ProviderOutcome(provider, ProviderStatus.RATE_LIMITED, error_code="rate_limited", error_message="servis kullanım sınırına ulaşıldı.")
    if status_code in {401, 403}:
        return ProviderOutcome(provider, ProviderStatus.UNAUTHORIZED, error_code="authentication_failed", error_message="servis erişim anahtarı kabul edilmedi.")
    if status_code >= 500:
        return ProviderOutcome(provider, ProviderStatus.UNAVAILABLE, error_code="provider_unavailable", error_message="güvenlik servisi geçici olarak yanıt vermiyor.")
    return ProviderOutcome(provider, ProviderStatus.ERROR, error_code="provider_request_rejected", error_message=f"güvenlik servisi isteği reddetti ({status_code}).")

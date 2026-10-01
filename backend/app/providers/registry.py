import asyncio
from collections.abc import Sequence

from app.core.config import get_settings
from app.providers.base import ProviderOutcome, ProviderStatus, ReputationProvider, Verdict
from app.providers.google_safe_browsing import GoogleSafeBrowsingProvider
from app.providers.urlhaus import URLhausProvider
from app.providers.virustotal import VirusTotalProvider


def get_providers() -> list[ReputationProvider]:
    settings = get_settings()
    return [
        VirusTotalProvider(settings.virustotal_api_key),
        GoogleSafeBrowsingProvider(settings.google_safe_browsing_api_key),
        URLhausProvider(settings.urlhaus_auth_key),
    ]


async def run_providers(url: str, providers: Sequence[ReputationProvider] | None = None) -> list[ProviderOutcome]:
    selected = list(providers if providers is not None else get_providers())
    outcomes = await asyncio.gather(*(provider.lookup(url) for provider in selected), return_exceptions=True)
    results: list[ProviderOutcome] = []
    for provider, result in zip(selected, outcomes, strict=True):
        if isinstance(result, BaseException):
            results.append(ProviderOutcome(
                provider=provider.name,
                status=ProviderStatus.ERROR,
                verdict=Verdict.UNKNOWN,
                error_code="adapter_error",
                error_message="sağlayıcı yanıtı işlenirken beklenmeyen bir hata oluştu.",
            ))
        else:
            results.append(result)
    return results

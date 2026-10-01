import asyncio

import httpx

from app.providers.base import ProviderStatus, Verdict
from app.providers.google_safe_browsing import GoogleSafeBrowsingProvider
from app.providers.urlhaus import URLhausProvider
from app.providers.virustotal import VirusTotalProvider


def client_factory_for(handler):
    transport = httpx.MockTransport(handler)
    return lambda **kwargs: httpx.AsyncClient(transport=transport, **kwargs)


def test_provider_without_key_is_explicitly_not_configured():
    for provider in (VirusTotalProvider(None), GoogleSafeBrowsingProvider(""), URLhausProvider(None)):
        outcome = asyncio.run(provider.lookup("https://example.com/"))
        assert outcome.status == ProviderStatus.NOT_CONFIGURED
        assert outcome.verdict == Verdict.UNKNOWN


def test_virustotal_uses_documented_unpadded_urlsafe_identifier_and_real_counts():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["key"] = request.headers.get("x-apikey")
        return httpx.Response(200, json={"data": {"attributes": {"last_analysis_stats": {
            "malicious": 1, "suspicious": 0, "harmless": 5, "undetected": 10, "timeout": 0,
        }}}})

    provider = VirusTotalProvider("test-key-only", client_factory_for(handler))
    outcome = asyncio.run(provider.lookup("https://example.com/"))
    assert seen["path"].endswith(VirusTotalProvider.url_identifier("https://example.com/"))
    assert "=" not in seen["path"].rsplit("/", 1)[-1]
    assert seen["key"] == "test-key-only"
    assert outcome.verdict == Verdict.MALICIOUS
    assert outcome.details["analysis_counts"]["malicious"] == 1


def test_virustotal_harmless_is_provider_reported_clean_only_when_no_flags():
    provider = VirusTotalProvider("test-key", client_factory_for(lambda request: httpx.Response(
        200, json={"data": {"attributes": {"last_analysis_stats": {"harmless": 3, "undetected": 7}}}}
    )))
    outcome = asyncio.run(provider.lookup("https://example.com/"))
    assert outcome.verdict == Verdict.CLEAN


def test_google_no_match_is_unknown_not_clean():
    provider = GoogleSafeBrowsingProvider("test-key", client_factory_for(lambda request: httpx.Response(200, json={})))
    outcome = asyncio.run(provider.lookup("https://example.com/"))
    assert outcome.status == ProviderStatus.NO_DATA
    assert outcome.verdict == Verdict.UNKNOWN


def test_google_match_is_based_on_provider_response():
    provider = GoogleSafeBrowsingProvider("test-key", client_factory_for(lambda request: httpx.Response(
        200, json={"matches": [{"threatType": "SOCIAL_ENGINEERING", "platformType": "ANY_PLATFORM", "threatEntryType": "URL"}]}
    )))
    outcome = asyncio.run(provider.lookup("https://example.com/"))
    assert outcome.verdict == Verdict.MALICIOUS
    assert outcome.details["matches"][0]["threat_type"] == "SOCIAL_ENGINEERING"


def test_urlhaus_no_results_is_unknown_not_clean():
    provider = URLhausProvider("test-key", client_factory_for(lambda request: httpx.Response(200, json={"query_status": "no_results"})))
    outcome = asyncio.run(provider.lookup("https://example.com/"))
    assert outcome.status == ProviderStatus.NO_DATA
    assert outcome.verdict == Verdict.UNKNOWN


def test_provider_rate_limit_is_separated_from_other_errors():
    provider = URLhausProvider("test-key", client_factory_for(lambda request: httpx.Response(429, json={})))
    outcome = asyncio.run(provider.lookup("https://example.com/"))
    assert outcome.status == ProviderStatus.RATE_LIMITED

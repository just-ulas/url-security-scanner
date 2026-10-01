from collections.abc import Callable
from typing import Any

import httpx

from app.providers.base import ProviderOutcome, ProviderStatus, Verdict, http_error_outcome


class GoogleSafeBrowsingProvider:
    name = "google_safe_browsing"
    endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

    def __init__(self, api_key: str | None, client_factory: Callable[..., Any] = httpx.AsyncClient):
        self.api_key = api_key.strip() if api_key else ""
        self.client_factory = client_factory

    async def lookup(self, url: str) -> ProviderOutcome:
        if not self.api_key:
            return ProviderOutcome(self.name, ProviderStatus.NOT_CONFIGURED, error_code="missing_api_key", error_message="google safe browsing erişim anahtarı ayarlanmamış.")
        body = {
            "client": {"clientId": "url-security-scanner", "clientVersion": "0.2.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        try:
            async with self.client_factory(timeout=httpx.Timeout(8.0), follow_redirects=False) as client:
                response = await client.post(self.endpoint, params={"key": self.api_key}, json=body)
        except (TimeoutError, httpx.TimeoutException):
            return ProviderOutcome(self.name, ProviderStatus.TIMEOUT, error_code="timeout", error_message="google safe browsing zamanında yanıt vermedi.")
        except httpx.HTTPError:
            return ProviderOutcome(self.name, ProviderStatus.UNAVAILABLE, error_code="network_error", error_message="google safe browsing hizmetine ulaşılamadı.")
        if response.status_code != 200:
            return http_error_outcome(self.name, response.status_code)
        try:
            payload = response.json()
            matches = payload.get("matches", [])
            if not isinstance(matches, list):
                raise TypeError("matches must be a list")
        except (ValueError, TypeError, AttributeError):
            return ProviderOutcome(self.name, ProviderStatus.ERROR, error_code="invalid_response", error_message="google safe browsing yanıtı beklenen biçimde değildi.")
        if not matches:
            return ProviderOutcome(
                self.name,
                ProviderStatus.NO_DATA,
                Verdict.UNKNOWN,
                {"match_count": 0, "meaning": "google listelerinde eşleşme bulunmadı; bu, bağlantının güvenli olduğunu kanıtlamaz."},
            )
        safe_matches = []
        for match in matches[:20]:
            safe_matches.append({
                "threat_type": str(match.get("threatType", "unknown")),
                "platform_type": str(match.get("platformType", "unknown")),
                "threat_entry_type": str(match.get("threatEntryType", "unknown")),
            })
        return ProviderOutcome(self.name, ProviderStatus.COMPLETED, Verdict.MALICIOUS, {"match_count": len(matches), "matches": safe_matches})

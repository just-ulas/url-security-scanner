import base64
from collections.abc import Callable
from typing import Any

import httpx

from app.providers.base import ProviderOutcome, ProviderStatus, Verdict, http_error_outcome


class VirusTotalProvider:
    name = "virustotal"
    base_url = "https://www.virustotal.com/api/v3/urls/"

    def __init__(self, api_key: str | None, client_factory: Callable[..., Any] = httpx.AsyncClient):
        self.api_key = api_key.strip() if api_key else ""
        self.client_factory = client_factory

    @staticmethod
    def url_identifier(url: str) -> str:
        return base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")

    async def lookup(self, url: str) -> ProviderOutcome:
        if not self.api_key:
            return ProviderOutcome(self.name, ProviderStatus.NOT_CONFIGURED, error_code="missing_api_key", error_message="virustotal erişim anahtarı ayarlanmamış.")
        try:
            async with self.client_factory(timeout=httpx.Timeout(8.0), follow_redirects=False) as client:
                response = await client.get(
                    self.base_url + self.url_identifier(url),
                    headers={"x-apikey": self.api_key, "accept": "application/json"},
                )
        except (TimeoutError, httpx.TimeoutException):
            return ProviderOutcome(self.name, ProviderStatus.TIMEOUT, error_code="timeout", error_message="virustotal zamanında yanıt vermedi.")
        except httpx.HTTPError:
            return ProviderOutcome(self.name, ProviderStatus.UNAVAILABLE, error_code="network_error", error_message="virustotal hizmetine ulaşılamadı.")
        if response.status_code == 404:
            return ProviderOutcome(self.name, ProviderStatus.NO_DATA, error_code="no_report", error_message="virustotal bu adres için rapor bulamadı.")
        if response.status_code != 200:
            return http_error_outcome(self.name, response.status_code)
        try:
            payload = response.json()
            attributes = payload["data"]["attributes"]
            stats = attributes.get("last_analysis_stats", {})
            counts = {key: max(0, int(stats.get(key, 0) or 0)) for key in ("malicious", "suspicious", "harmless", "undetected", "timeout")}
        except (ValueError, TypeError, KeyError, AttributeError):
            return ProviderOutcome(self.name, ProviderStatus.ERROR, error_code="invalid_response", error_message="virustotal yanıtı beklenen biçimde değildi.")
        if counts["malicious"]:
            verdict = Verdict.MALICIOUS
        elif counts["suspicious"]:
            verdict = Verdict.SUSPICIOUS
        elif counts["harmless"]:
            verdict = Verdict.CLEAN
        else:
            verdict = Verdict.UNKNOWN
        details = {
            "analysis_counts": counts,
            "last_analysis_date": attributes.get("last_analysis_date"),
            "meaning": "harmless yalnızca virustotal motorlarının zararsız dediği bildirim sayısıdır; undetected sonuç değildir.",
        }
        return ProviderOutcome(self.name, ProviderStatus.COMPLETED, verdict, details)

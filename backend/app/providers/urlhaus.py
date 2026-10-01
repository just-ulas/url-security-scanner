from collections.abc import Callable
from typing import Any

import httpx

from app.providers.base import ProviderOutcome, ProviderStatus, Verdict, http_error_outcome


class URLhausProvider:
    name = "urlhaus"
    endpoint = "https://urlhaus-api.abuse.ch/v1/url/"

    def __init__(self, auth_key: str | None, client_factory: Callable[..., Any] = httpx.AsyncClient):
        self.auth_key = auth_key.strip() if auth_key else ""
        self.client_factory = client_factory

    async def lookup(self, url: str) -> ProviderOutcome:
        if not self.auth_key:
            return ProviderOutcome(self.name, ProviderStatus.NOT_CONFIGURED, error_code="missing_api_key", error_message="urlhaus erişim anahtarı ayarlanmamış.")
        try:
            async with self.client_factory(timeout=httpx.Timeout(8.0), follow_redirects=False) as client:
                response = await client.post(
                    self.endpoint,
                    headers={"Auth-Key": self.auth_key, "accept": "application/json"},
                    data={"url": url},
                )
        except (TimeoutError, httpx.TimeoutException):
            return ProviderOutcome(self.name, ProviderStatus.TIMEOUT, error_code="timeout", error_message="urlhaus zamanında yanıt vermedi.")
        except httpx.HTTPError:
            return ProviderOutcome(self.name, ProviderStatus.UNAVAILABLE, error_code="network_error", error_message="urlhaus hizmetine ulaşılamadı.")
        if response.status_code != 200:
            return http_error_outcome(self.name, response.status_code)
        try:
            payload = response.json()
            query_status = payload.get("query_status")
        except (ValueError, TypeError, AttributeError):
            return ProviderOutcome(self.name, ProviderStatus.ERROR, error_code="invalid_response", error_message="urlhaus yanıtı beklenen biçimde değildi.")
        if query_status == "no_results":
            return ProviderOutcome(
                self.name,
                ProviderStatus.NO_DATA,
                Verdict.UNKNOWN,
                {"meaning": "urlhaus kaydı bulunmadı; bu, bağlantının güvenli olduğunu kanıtlamaz."},
            )
        if query_status != "ok" or not isinstance(payload.get("url"), str):
            return ProviderOutcome(self.name, ProviderStatus.ERROR, error_code="unexpected_response", error_message="urlhaus sorgu durumunu doğrulayamadı.")
        return ProviderOutcome(
            self.name,
            ProviderStatus.COMPLETED,
            Verdict.MALICIOUS,
            {
                "url_status": payload.get("url_status"),
                "threat": payload.get("threat"),
                "date_added": payload.get("date_added"),
                "tags": payload.get("tags") if isinstance(payload.get("tags"), list) else [],
                "report_id": payload.get("id"),
            },
        )

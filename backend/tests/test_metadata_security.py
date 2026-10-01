import asyncio
from urllib.parse import urljoin

import pytest

from app.services.metadata import PinnedResolver, resolve_public_addresses
from app.services.url_policy import UnsafeTargetError, normalize_url


class FakeLoop:
    async def getaddrinfo(self, host, port, type):
        return [(2, 1, 6, "", ("93.184.216.34", port))]


def test_dns_results_are_pinned_for_the_connection(monkeypatch):
    monkeypatch.setattr("app.services.metadata.asyncio.get_running_loop", lambda: FakeLoop())
    addresses = asyncio.run(resolve_public_addresses("example.com", 443))
    pinned = PinnedResolver("example.com", addresses)
    records = asyncio.run(pinned.resolve("example.com", 443))
    assert [item["host"] for item in records] == ["93.184.216.34"]
    with pytest.raises(OSError):
        asyncio.run(pinned.resolve("other.example", 443))


def test_dns_response_with_any_private_address_is_blocked(monkeypatch):
    class MixedLoop:
        async def getaddrinfo(self, host, port, type):
            return [
                (2, 1, 6, "", ("93.184.216.34", port)),
                (2, 1, 6, "", ("169.254.169.254", port)),
            ]

    monkeypatch.setattr("app.services.metadata.asyncio.get_running_loop", lambda: MixedLoop())
    with pytest.raises(UnsafeTargetError):
        asyncio.run(resolve_public_addresses("rebinding.example", 443))


def test_redirect_to_private_address_is_rejected_before_request():
    original = normalize_url("https://example.com/start")
    destination = urljoin(original.url, "http://127.0.0.1/admin")
    with pytest.raises(UnsafeTargetError):
        normalize_url(destination)


def test_redirect_to_private_hostname_is_rejected():
    with pytest.raises(UnsafeTargetError):
        normalize_url("http://metadata.google.internal/computeMetadata/v1/")

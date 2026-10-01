from __future__ import annotations

import asyncio
import ipaddress
import socket
import ssl
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import aiohttp
from aiohttp.abc import AbstractResolver
from cryptography import x509
from cryptography.hazmat.primitives import hashes

from app.services.url_policy import (
    NormalizedURL,
    UnsafeTargetError,
    is_public_ip,
    normalize_url,
)

MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 256 * 1024
CONNECT_TIMEOUT_SECONDS = 4
TOTAL_TIMEOUT_SECONDS = 12
REDIRECT_CODES = {301, 302, 303, 307, 308}
SAFE_RESPONSE_HEADERS = {
    "cache-control", "content-length", "content-type", "date", "etag", "expires",
    "last-modified", "location", "pragma", "referrer-policy", "server",
    "strict-transport-security", "content-security-policy", "x-content-type-options",
    "x-frame-options", "x-powered-by", "permissions-policy",
}
SECURITY_HEADER_NAMES = {
    "strict-transport-security", "content-security-policy", "x-content-type-options",
    "x-frame-options", "referrer-policy", "permissions-policy",
}


class PinnedResolver(AbstractResolver):
    """aiohttp resolver that can return only addresses checked for this request hop."""

    def __init__(self, hostname: str, addresses: list[str]):
        self.hostname = hostname
        self.addresses = addresses

    async def resolve(self, host: str, port: int = 0, family: int = socket.AF_INET):
        if host.rstrip(".").lower() != self.hostname.rstrip(".").lower():
            raise OSError("dns pin did not match the requested host")
        records = []
        for address in self.addresses:
            parsed = ipaddress.ip_address(address)
            records.append({
                "hostname": host,
                "host": address,
                "port": port,
                "family": socket.AF_INET6 if parsed.version == 6 else socket.AF_INET,
                "proto": 0,
                "flags": socket.AI_NUMERICHOST,
            })
        return records

    async def close(self) -> None:
        return None


async def resolve_public_addresses(hostname: str, port: int) -> list[str]:
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise OSError("alan adı çözümlenemedi.") from exc
        addresses = sorted({item[4][0] for item in infos})
    else:
        addresses = [literal.compressed]
    if not addresses:
        raise OSError("alan adı için ip adresi bulunamadı.")
    if any(not is_public_ip(address) for address in addresses):
        raise UnsafeTargetError("alan adı yerel veya genel erişime kapalı bir ip adresine çözülüyor.")
    return addresses


def _clean_header(value: str, max_length: int = 512) -> str:
    return "".join(char for char in value if ord(char) >= 32 and ord(char) != 127)[:max_length]


def _tls_summary(response: aiohttp.ClientResponse, scheme: str) -> dict[str, Any]:
    if scheme != "https":
        return {"status": "not_applicable"}
    connection = response.connection
    transport = connection.transport if connection else None
    ssl_object = transport.get_extra_info("ssl_object") if transport else None
    if ssl_object is None:
        return {"status": "unavailable", "reason": "tls certificate details were not exposed by the connection"}
    der = ssl_object.getpeercert(binary_form=True)
    if not der:
        return {"status": "unavailable", "reason": "peer certificate was not available"}
    certificate = x509.load_der_x509_certificate(der)
    return {
        "status": "verified",
        "version": ssl_object.version(),
        "subject": certificate.subject.rfc4514_string(),
        "issuer": certificate.issuer.rfc4514_string(),
        "not_before": certificate.not_valid_before_utc.isoformat(),
        "not_after": certificate.not_valid_after_utc.isoformat(),
        "sha256_fingerprint": certificate.fingerprint(hashes.SHA256()).hex(),
    }


def _headers_summary(headers: aiohttp.typedefs.LooseHeaders) -> tuple[dict[str, str], dict[str, str | None]]:
    lowered = {str(key).lower(): _clean_header(str(value)) for key, value in headers.items()}
    selected = {key: lowered[key] for key in SAFE_RESPONSE_HEADERS if key in lowered}
    security = {key: lowered.get(key) for key in sorted(SECURITY_HEADER_NAMES)}
    return selected, security


def _unavailable(reason: str, dns_hops: list[dict[str, Any]], redirect_chain: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": reason,
        "dns": {"status": "observed" if dns_hops else "unavailable", "hops": dns_hops},
        "resolved_ips": sorted({ip for hop in dns_hops for ip in hop["addresses"]}),
        "redirect_chain": redirect_chain,
        "http": {"status": "unavailable"},
        "tls": {"status": "unavailable"},
        "asn": {"status": "unavailable", "reason": "asn provider is not configured"},
        "domain": {"status": "unavailable", "reason": "domain registration provider is not configured"},
        "detected_technologies": {"status": "unavailable", "items": []},
    }


async def inspect_url(raw_url: str) -> dict[str, Any]:
    current_url = normalize_url(raw_url).url
    redirect_chain: list[dict[str, Any]] = []
    dns_hops: list[dict[str, Any]] = []
    seen: set[str] = set()
    final: dict[str, Any] | None = None

    for hop_number in range(MAX_REDIRECTS + 1):
        target: NormalizedURL = normalize_url(current_url)
        if target.url in seen:
            return _unavailable("redirect loop detected", dns_hops, redirect_chain)
        seen.add(target.url)
        try:
            addresses = await resolve_public_addresses(target.hostname, target.port)
        except UnsafeTargetError:
            raise
        except OSError as exc:
            return _unavailable(str(exc), dns_hops, redirect_chain)
        dns_hops.append({
            "hostname": target.hostname,
            "addresses": addresses,
            "observed_at": datetime.now(UTC).isoformat(),
        })

        resolver = PinnedResolver(target.hostname, addresses)
        timeout = aiohttp.ClientTimeout(
            total=TOTAL_TIMEOUT_SECONDS,
            connect=CONNECT_TIMEOUT_SECONDS,
            sock_read=5,
        )
        connector = aiohttp.TCPConnector(
            resolver=resolver,
            use_dns_cache=False,
            ssl=ssl.create_default_context(),
            force_close=True,
            limit=1,
        )
        try:
            async with (
                aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    trust_env=False,
                    auto_decompress=True,
                    headers={"User-Agent": "url-security-scanner-beta/0.2", "Accept": "*/*"},
                ) as session,
                session.get(
                    target.url,
                    allow_redirects=False,
                    headers={"Range": f"bytes=0-{MAX_RESPONSE_BYTES - 1}"},
                ) as response,
            ):
                    response_headers, security_headers = _headers_summary(response.headers)
                    tls = _tls_summary(response, target.scheme)
                    status_code = response.status
                    location = response.headers.get("Location")
                    body_read = 0
                    body_truncated = False
                    if status_code not in REDIRECT_CODES or not location:
                        content_length = response.content_length
                        if content_length is None or content_length <= MAX_RESPONSE_BYTES:
                            sample = await response.content.read(MAX_RESPONSE_BYTES + 1)
                            body_read = min(len(sample), MAX_RESPONSE_BYTES)
                            body_truncated = len(sample) > MAX_RESPONSE_BYTES
                        else:
                            body_truncated = True
                    final = {
                        "status": "observed",
                        "dns": {"status": "observed", "hops": dns_hops},
                        "resolved_ips": sorted({ip for item in dns_hops for ip in item["addresses"]}),
                        "redirect_chain": redirect_chain,
                        "http": {
                            "status": status_code,
                            "final_url": target.url,
                            "headers": response_headers,
                            "security_headers": security_headers,
                            "body_bytes_read": body_read,
                            "body_limit_bytes": MAX_RESPONSE_BYTES,
                            "body_truncated": body_truncated,
                            "body_stored": False,
                        },
                        "tls": tls,
                        "asn": {"status": "unavailable", "reason": "asn provider is not configured"},
                        "domain": {"status": "unavailable", "reason": "domain registration provider is not configured"},
                        "detected_technologies": {
                            "status": "header_hints_only",
                            "items": [
                                {"name": name, "value": response_headers[name], "source": "http_header"}
                                for name in ("server", "x-powered-by") if name in response_headers
                            ],
                        },
                    }
                    if status_code in REDIRECT_CODES and location:
                        if hop_number >= MAX_REDIRECTS:
                            final["status"] = "redirect_limit_reached"
                            final["http"]["redirect_limit"] = MAX_REDIRECTS
                            return final
                        next_url = urljoin(target.url, location)
                        try:
                            next_target = normalize_url(next_url)
                        except (ValueError, UnsafeTargetError) as exc:
                            redirect_chain.append({"url": target.url, "status": status_code, "destination": "blocked", "reason": str(exc)})
                            final["status"] = "redirect_blocked"
                            final["redirect_chain"] = redirect_chain
                            return final
                        redirect_chain.append({"url": target.url, "status": status_code, "destination": next_target.url})
                        current_url = next_target.url
                        continue
                    final["redirect_chain"] = redirect_chain
                    return final
        except UnsafeTargetError:
            raise
        except (TimeoutError, aiohttp.ClientError, ssl.SSLError, OSError, ValueError) as exc:
            return _unavailable(f"target request failed: {type(exc).__name__}", dns_hops, redirect_chain)
    return final or _unavailable("scan did not produce an http response", dns_hops, redirect_chain)

"""Input hygiene only. This module does not resolve or fetch hostnames."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit


class URLPolicyError(ValueError):
    """Submitted value is not an allowed HTTP(S) URL."""


def validate_submitted_url(value: str) -> str:
    """Validate a URL's syntax and deny literal non-global IPs; do not make a request."""
    if not value or value != value.strip() or any(ord(char) < 32 for char in value):
        raise URLPolicyError("URL must be non-empty and contain no surrounding whitespace/control characters")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        # Accessing .port validates malformed/out-of-range port syntax.
        _ = parsed.port
    except ValueError as exc:
        raise URLPolicyError("URL has invalid authority or port syntax") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise URLPolicyError("Only http and https URLs are accepted")
    if not parsed.netloc or not hostname:
        raise URLPolicyError("URL must contain a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise URLPolicyError("URLs containing embedded credentials are not accepted")

    normalized_host = hostname.rstrip(".").lower()
    if not normalized_host:
        raise URLPolicyError("URL must contain a hostname")
    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError:
        # DNS resolution is deliberately absent: a hostname could resolve to a private IP.
        return value
    if not address.is_global:
        raise URLPolicyError("Literal IP address must be globally routable")
    return value

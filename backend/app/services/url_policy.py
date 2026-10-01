import hashlib
import ipaddress
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


class URLPolicyError(ValueError):
    """istek biçimindeki sorunları bildirir."""


class UnsafeTargetError(URLPolicyError):
    """yerel veya genel erişime kapalı bir hedefi bildirir."""


@dataclass(frozen=True)
class NormalizedURL:
    url: str
    scheme: str
    hostname: str
    port: int
    fingerprint: str


def is_public_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if getattr(address, "ipv4_mapped", None) is not None:
        address = address.ipv4_mapped
    return bool(
        address.is_global
        and not (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        )
    )


def normalize_url(value: str) -> NormalizedURL:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise URLPolicyError("adres boş olamaz ve 2048 karakteri aşamaz.")
    if value != value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise URLPolicyError("adresin başında/sonunda boşluk veya kontrol karakteri olamaz.")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        explicit_port = parsed.port
    except ValueError as exc:
        raise URLPolicyError("adresin sunucu veya port bölümü geçersiz.") from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise URLPolicyError("yalnızca http ve https bağlantıları kabul ediliyor.")
    if not parsed.netloc or not hostname:
        raise URLPolicyError("adreste bir alan adı bulunmalı.")
    if parsed.username is not None or parsed.password is not None:
        raise URLPolicyError("kullanıcı adı veya parola içeren bağlantılar kabul edilmiyor.")

    hostname = hostname.rstrip(".").lower()
    if not hostname or hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal")):
        raise UnsafeTargetError("yerel veya şirket içi alan adları taranamaz.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            hostname = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise URLPolicyError("alan adı biçimi geçersiz.") from exc
        if len(hostname) > 253 or any(not label or len(label) > 63 for label in hostname.split(".")):
            raise URLPolicyError("alan adı biçimi geçersiz.")
    else:
        if not is_public_ip(str(address)):
            raise UnsafeTargetError("yerel, özel veya ayrılmış ip adresleri taranamaz.")
        hostname = address.compressed

    default_port = 80 if scheme == "http" else 443
    if explicit_port is not None and explicit_port != default_port:
        raise URLPolicyError("yalnızca http için 80, https için 443 numaralı bağlantı noktaları kabul ediliyor.")
    port = default_port
    host_for_url = f"[{hostname}]" if ":" in hostname else hostname
    path = parsed.path or "/"
    normalized = urlunsplit((scheme, host_for_url, path, parsed.query, ""))
    fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return NormalizedURL(normalized, scheme, hostname, port, fingerprint)

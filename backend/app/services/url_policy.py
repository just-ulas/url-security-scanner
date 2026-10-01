"""yalnızca adres biçimini kontrol eder; alan adını çözümlemez veya bağlantı açmaz."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit


class URLPolicyError(ValueError):
    """gönderilen adres izin verilen http/https biçiminde değil."""


def validate_submitted_url(value: str) -> str:
    """adres biçimini denetler ve genel olmayan ip'leri reddeder; istek göndermez."""
    if not value or value != value.strip() or any(ord(char) < 32 for char in value):
        raise URLPolicyError("adres boş olamaz; başında veya sonunda boşluk bulunmamalı.")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        # .port alanına erişmek, bozuk veya sınır dışı port bilgisini yakalar.
        _ = parsed.port
    except ValueError as exc:
        raise URLPolicyError("adresin sunucu ya da port bölümü geçersiz görünüyor.") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise URLPolicyError("yalnızca http veya https bağlantıları kabul ediliyor.")
    if not parsed.netloc or not hostname:
        raise URLPolicyError("adreste bir alan adı bulunmalı.")
    if parsed.username is not None or parsed.password is not None:
        raise URLPolicyError("kullanıcı adı veya parola içeren bağlantılar kabul edilmiyor.")

    normalized_host = hostname.rstrip(".").lower()
    if not normalized_host:
        raise URLPolicyError("adreste bir alan adı bulunmalı.")
    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError:
        # dns sorgusu bilerek yapılmıyor: alan adı özel bir ip'ye çözülebilir.
        return value
    if not address.is_global:
        raise URLPolicyError("bu ip adresi genel internete açık değil.")
    return value

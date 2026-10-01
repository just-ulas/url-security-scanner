import pytest

from app.services.url_policy import UnsafeTargetError, is_public_ip, normalize_url


@pytest.mark.parametrize("address", [
    "127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.1.1", "169.254.169.254",
    "0.0.0.0", "::1", "fc00::1", "fe80::1", "::ffff:127.0.0.1",
])
def test_non_public_ip_literals_are_rejected(address):
    with pytest.raises(UnsafeTargetError):
        normalize_url(f"http://[{address}]/" if ":" in address else f"http://{address}/")


def test_public_address_classifier_checks_v4_and_v6():
    assert is_public_ip("8.8.8.8")
    assert is_public_ip("2606:4700:4700::1111")
    assert not is_public_ip("100.64.0.1")
    assert not is_public_ip("::ffff:127.0.0.1")


def test_normalizes_case_default_port_and_drops_fragment():
    result = normalize_url("HTTPS://ExAmPlE.com:443/a?x=1#private-fragment")
    assert result.url == "https://example.com/a?x=1"
    assert result.scheme == "https"
    assert result.hostname == "example.com"
    assert len(result.fingerprint) == 64


def test_idna_domain_is_ascii_normalized():
    result = normalize_url("https://bücher.example/")
    assert result.hostname == "xn--bcher-kva.example"


@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "ftp://example.com/", "http://user@example.com/",
    "http://example.com:0/", "https://example.com:444/", "http://example.com\n/",
    "http://example.com/" + "x" * 2048,
])
def test_rejects_invalid_urls(url):
    with pytest.raises(ValueError):
        normalize_url(url)


def test_local_names_are_rejected():
    for host in ("localhost", "admin.localhost", "router.local", "db.internal"):
        with pytest.raises(UnsafeTargetError):
            normalize_url(f"http://{host}/")

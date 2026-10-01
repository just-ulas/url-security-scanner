"""ileride güvenlik servisiyle çalışacak arka plan işinin yeri."""


def execute_scan(scan_id: str) -> None:
    """kalıcı iş kuyruğu ve gerçek servisler hazır olana kadar tarama yapmaz."""
    raise NotImplementedError(
        f"tarama işçisi henüz hazır değil; {scan_id!r} hiçbir güvenlik servisine gönderilmedi."
    )

"""Queue task entry point reserved for a future provider-backed worker."""


def execute_scan(scan_id: str) -> None:
    """Refuse to imply a scan happened until durable jobs and provider adapters exist."""
    raise NotImplementedError(
        f"Scan worker is disabled; scan {scan_id!r} was not submitted to any provider."
    )

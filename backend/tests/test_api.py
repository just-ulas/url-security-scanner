from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_only_reports_process_health() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scan_execution": "disabled"}


def test_valid_url_does_not_claim_a_scan_was_run() -> None:
    response = client.post("/api/v1/scans", json={"url": "https://example.com/path"})
    assert response.status_code == 501
    assert "No provider was called" in response.json()["detail"]


def test_rejects_non_http_scheme() -> None:
    response = client.post("/api/v1/scans", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422


def test_rejects_private_literal_ip() -> None:
    response = client.post("/api/v1/scans", json={"url": "http://127.0.0.1/"})
    assert response.status_code == 422


def test_rejects_embedded_credentials() -> None:
    response = client.post("/api/v1/scans", json={"url": "https://alice:secret@example.com/"})
    assert response.status_code == 422

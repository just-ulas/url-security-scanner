from rq import Queue

from app.services.scans import QUEUE_NAME


def test_scan_is_queued_and_has_no_fabricated_provider_results(client, fake_redis):
    response = client.post("/api/scans", json={"url": "https://example.com/path#fragment"})
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["overall_verdict"] == "unknown"
    assert body["providers"] == []
    assert body["url"] == "https://example.com/path"
    assert Queue(QUEUE_NAME, connection=fake_redis).count == 1
    assert response.headers["location"] == f"/api/scans/{body['id']}"


def test_polling_reads_queued_status_and_results(client):
    created = client.post("/api/scans", json={"url": "https://example.com/"}).json()
    response = client.get(f"/api/scans/{created['id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    results = client.get(f"/api/scans/{created['id']}/results").json()
    assert results["overall_verdict"] == "unknown"
    assert results["providers"] == []


def test_duplicate_in_progress_scan_reuses_existing_job(client, fake_redis):
    first = client.post("/api/scans", json={"url": "https://example.com/a#one"}).json()
    second_response = client.post("/api/scans", json={"url": "https://example.com/a#two"})
    assert second_response.status_code == 202
    second = second_response.json()
    assert second["id"] == first["id"]
    assert second["deduplicated"] is True
    assert Queue(QUEUE_NAME, connection=fake_redis).count == 1


def test_rejects_private_or_credential_urls_before_queueing(client, fake_redis):
    for url in (
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://user:pass@example.com/",
        "http://localhost/",
        "http://example.com:8080/",
    ):
        response = client.post("/api/scans", json={"url": url})
        assert response.status_code == 422, url
    assert Queue(QUEUE_NAME, connection=fake_redis).count == 0


def test_scan_rate_limit_returns_429(client):
    responses = [client.post("/api/scans", json={"url": f"https://example.com/{i}"}) for i in range(6)]
    assert all(item.status_code == 202 for item in responses[:5])
    assert responses[5].status_code == 429

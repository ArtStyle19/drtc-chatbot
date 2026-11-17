import httpx


async def test_liveness_probe(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_reports_an_unreachable_database(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["checks"] == {"database": "unavailable", "corpus_manifest": "ok"}


async def test_unknown_routes_return_problem_details(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 404
    assert body["code"] == "http_404"
    assert body["request_id"] == response.headers["x-request-id"]


async def test_a_valid_incoming_request_id_is_propagated(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live", headers={"x-request-id": "req-abc-12345"})

    assert response.headers["x-request-id"] == "req-abc-12345"


async def test_an_unsafe_incoming_request_id_is_replaced(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live", headers={"x-request-id": "bad id with spaces"})

    assert response.headers["x-request-id"] != "bad id with spaces"
    assert len(response.headers["x-request-id"]) == 32

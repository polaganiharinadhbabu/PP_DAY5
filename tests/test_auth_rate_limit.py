def test_missing_invalid_and_valid_api_keys(
    client,
    auth_headers,
):
    assert client.get("/v1/notes").status_code == 401

    assert client.get(
        "/v1/notes",
        headers={"X-API-Key": "wrong-key"},
    ).status_code == 401

    assert client.get(
        "/v1/notes",
        headers=auth_headers,
    ).status_code == 200


def test_rate_limit_returns_429_and_retry_after(
    client,
    auth_headers,
    monkeypatch,
):
    import app.rate_limit as rate_limit

    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    rate_limit.reset_rate_limiter()

    first = client.get(
        "/v1/notes",
        headers=auth_headers,
    )
    assert first.status_code == 200

    second = client.get(
        "/v1/notes",
        headers=auth_headers,
    )

    assert second.status_code == 429
    assert "Retry-After" in second.headers
    assert (
        second.json()["detail"]["error"]
        == "rate_limit_exceeded"
    )

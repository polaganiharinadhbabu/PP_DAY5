def test_create_read_update_delete_note(
    client,
    auth_headers,
):
    response = client.post(
        "/v1/notes",
        headers=auth_headers,
        json={
            "title": "First note",
            "body": "Hello world",
        },
    )

    assert response.status_code == 201
    note = response.json()

    assert note["title"] == "First note"
    assert note["status"] == "draft"

    assert client.get(
        f"/v1/notes/{note['id']}",
        headers=auth_headers,
    ).status_code == 200

    updated = client.patch(
        f"/v1/notes/{note['id']}",
        headers=auth_headers,
        json={"status": "published"},
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "published"

    deleted = client.delete(
        f"/v1/notes/{note['id']}",
        headers=auth_headers,
    )

    assert deleted.status_code == 204

    assert client.get(
        f"/v1/notes/{note['id']}",
        headers=auth_headers,
    ).status_code == 404


def test_validation_missing_id_and_duplicate_title(
    client,
    auth_headers,
):
    assert client.post(
        "/v1/notes",
        headers=auth_headers,
        json={"title": ""},
    ).status_code == 422

    assert client.get(
        "/v1/notes/999",
        headers=auth_headers,
    ).status_code == 404

    payload = {"title": "Duplicate"}

    assert client.post(
        "/v1/notes",
        headers=auth_headers,
        json=payload,
    ).status_code == 201

    assert client.post(
        "/v1/notes",
        headers=auth_headers,
        json=payload,
    ).status_code == 409


def test_search_pagination_and_sort_allowlist(
    client,
    auth_headers,
):
    notes = [
        {"title": "Alpha", "status": "draft"},
        {"title": "Beta", "status": "published"},
        {"title": "Another Alpha", "status": "draft"},
    ]

    for note in notes:
        assert client.post(
            "/v1/notes",
            headers=auth_headers,
            json=note,
        ).status_code == 201

    response = client.get(
        "/v1/notes?q=Alpha&status=draft&limit=1&offset=0",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    assert client.get(
        "/v1/notes?limit=101",
        headers=auth_headers,
    ).status_code == 422

    assert client.get(
        "/v1/notes?offset=-1",
        headers=auth_headers,
    ).status_code == 422

    assert client.get(
        "/v1/notes?sort_by=invalid",
        headers=auth_headers,
    ).status_code == 422

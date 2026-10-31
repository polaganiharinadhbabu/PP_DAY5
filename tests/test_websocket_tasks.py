from unittest.mock import Mock


def test_websocket_echo_and_disconnect_cleanup(
    client,
    auth_headers,
):
    from app.main import room_manager

    key = auth_headers["X-API-Key"]

    with client.websocket_connect(
        f"/ws/notes?room=test-room&api_key={key}"
    ) as websocket:
        websocket.send_json({"message": "hello room"})

        assert websocket.receive_json() == {
            "room": "test-room",
            "message": "hello room",
        }

    assert "test-room" not in room_manager.rooms


def test_websocket_rejects_invalid_key(client):
    import pytest
    from fastapi.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws/notes?room=test-room&api_key=wrong-key"
        ):
            pass


def test_summary_task_accepted_and_queue_failure(
    client,
    auth_headers,
    monkeypatch,
):
    import app.main as main

    created = client.post(
        "/v1/notes",
        headers=auth_headers,
        json={
            "title": "Summary note",
            "body": "Text to summarize",
        },
    )

    note_id = created.json()["id"]
    fake_task = Mock(id="task-123")

    monkeypatch.setattr(
        main.generate_note_summary,
        "delay",
        lambda *args: fake_task,
    )

    queued = client.post(
        f"/v1/notes/{note_id}/summary",
        headers=auth_headers,
    )

    assert queued.status_code == 202
    assert queued.json()["task_id"] == "task-123"

    monkeypatch.setattr(
        main.generate_note_summary,
        "delay",
        Mock(side_effect=RuntimeError("Redis unavailable")),
    )

    failed = client.post(
        f"/v1/notes/{note_id}/summary",
        headers=auth_headers,
    )

    assert failed.status_code == 503

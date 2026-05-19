"""
Tests for the chat streaming endpoint:
  POST /chat/stream

The orchestrator is mocked so no real OpenAI calls are made.
"""

import json
import pytest
from unittest.mock import patch


def _parse_sse(text: str) -> list[dict]:
    """Parse SSE response text into a list of event dicts."""
    events = []
    for line in text.strip().split("\n"):
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events


async def _fake_stream(*args, **kwargs):
    """Mock async generator that yields a few tokens."""
    yield "Hello"
    yield " from"
    yield " the"
    yield " AI."


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_chat_stream_requires_auth(client):
    response = client.post("/chat/stream", json={"message": "Hello"})
    assert response.status_code == 401


def test_chat_stream_rejects_wrong_api_key(client):
    response = client.post(
        "/chat/stream",
        json={"message": "Hello"},
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401


# ── Streaming response ────────────────────────────────────────────────────────

def test_chat_stream_returns_200(client, auth):
    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "Hello"},
            headers=auth
        )
    assert response.status_code == 200


def test_chat_stream_content_type_is_sse(client, auth):
    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "Hello"},
            headers=auth
        )
    assert "text/event-stream" in response.headers["content-type"]


def test_chat_stream_returns_session_event(client, auth):
    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "Hello"},
            headers=auth
        )
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    assert "session" in types


def test_chat_stream_returns_token_events(client, auth):
    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "Hello"},
            headers=auth
        )
    events = _parse_sse(response.text)
    tokens = [e for e in events if e["type"] == "token"]
    assert len(tokens) > 0


def test_chat_stream_returns_done_event(client, auth):
    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "Hello"},
            headers=auth
        )
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    assert "done" in types


def test_chat_stream_session_id_is_string(client, auth):
    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "Hello"},
            headers=auth
        )
    events = _parse_sse(response.text)
    session_event = next(e for e in events if e["type"] == "session")
    assert isinstance(session_event["session_id"], str)
    assert len(session_event["session_id"]) > 0


def test_chat_stream_saves_to_history(client, auth):
    """Verify message is stored in session history after streaming."""
    from api.services.history import history_manager

    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        response = client.post(
            "/chat/stream",
            json={"message": "Save this message"},
            headers=auth
        )

    events = _parse_sse(response.text)
    session_event = next(e for e in events if e["type"] == "session")
    session_id = session_event["session_id"]

    messages = history_manager.get_messages(session_id)
    user_messages = [m for m in messages if m.role == "user"]
    assert any("Save this message" in m.content for m in user_messages)


def test_chat_stream_continues_existing_session(client, auth):
    """Sending the same session_id continues the conversation."""
    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        r1 = client.post("/chat/stream", json={"message": "First"}, headers=auth)
    events1 = _parse_sse(r1.text)
    session_id = next(e for e in events1 if e["type"] == "session")["session_id"]

    with patch("api.routes.chat.orchestrator.stream", side_effect=_fake_stream):
        r2 = client.post(
            "/chat/stream",
            json={"message": "Second", "session_id": session_id},
            headers=auth
        )
    events2 = _parse_sse(r2.text)
    returned_session_id = next(e for e in events2 if e["type"] == "session")["session_id"]
    assert returned_session_id == session_id

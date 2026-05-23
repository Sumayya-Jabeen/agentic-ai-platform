"""
Tests for session management endpoints:
  GET  /sessions
  GET  /history/{session_id}
  PATCH /sessions/{session_id}/rename
  DELETE /history/{session_id}

Uses history_manager directly to seed data — avoids real LLM calls.
"""

import pytest
from api.services.history import history_manager


@pytest.fixture(autouse=True)
def clean_history():
    """Clear all sessions before and after each test for isolation."""
    history_manager._sessions.clear()
    history_manager._titles.clear()
    yield
    history_manager._sessions.clear()
    history_manager._titles.clear()


def _seed_session(messages: list[tuple[str, str]]) -> str:
    """Helper: create a session and add messages. Returns session_id."""
    session_id = history_manager.create_session()
    for role, content in messages:
        history_manager.add_message(session_id, role, content)
    return session_id


# ── GET /sessions ─────────────────────────────────────────────────────────────

def test_sessions_returns_empty_list_initially(client, auth):
    response = client.get("/sessions", headers=auth)
    assert response.status_code == 200
    assert response.json()["sessions"] == []


def test_sessions_lists_active_sessions(client, auth):
    _seed_session([("user", "Hello"), ("assistant", "Hi!")])
    response = client.get("/sessions", headers=auth)
    assert response.status_code == 200
    assert len(response.json()["sessions"]) == 1


def test_sessions_title_derived_from_first_message(client, auth):
    _seed_session([("user", "What is machine learning?"), ("assistant", "It is...")])
    sessions = client.get("/sessions", headers=auth).json()["sessions"]
    assert "What is machine learning" in sessions[0]["title"]


def test_sessions_requires_auth(client):
    response = client.get("/sessions")
    assert response.status_code == 401


# ── GET /history/{session_id} ─────────────────────────────────────────────────

def test_history_returns_messages(client, auth):
    session_id = _seed_session([
        ("user", "Research AI agents"),
        ("assistant", "Here is what I found...")
    ])
    response = client.get(f"/history/{session_id}", headers=auth)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["total_messages"] == 2


def test_history_returns_correct_roles(client, auth):
    session_id = _seed_session([("user", "Hello"), ("assistant", "Hi!")])
    messages = client.get(f"/history/{session_id}", headers=auth).json()["messages"]
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_history_returns_correct_content(client, auth):
    session_id = _seed_session([("user", "Plan my project")])
    messages = client.get(f"/history/{session_id}", headers=auth).json()["messages"]
    assert messages[0]["content"] == "Plan my project"


def test_history_returns_404_for_unknown_session(client, auth):
    response = client.get("/history/nonexistent-session-id", headers=auth)
    assert response.status_code == 404


def test_history_requires_auth(client):
    session_id = _seed_session([("user", "Hello")])
    response = client.get(f"/history/{session_id}")
    assert response.status_code == 401


# ── PATCH /sessions/{session_id}/rename ──────────────────────────────────────

def test_rename_session_updates_title(client, auth):
    session_id = _seed_session([("user", "Original title message")])
    client.patch(
        f"/sessions/{session_id}/rename",
        json={"title": "My Custom Title"},
        headers=auth
    )
    sessions = client.get("/sessions", headers=auth).json()["sessions"]
    assert sessions[0]["title"] == "My Custom Title"


def test_rename_session_returns_200(client, auth):
    session_id = _seed_session([("user", "Hello")])
    response = client.patch(
        f"/sessions/{session_id}/rename",
        json={"title": "New Name"},
        headers=auth
    )
    assert response.status_code == 200


def test_rename_session_returns_404_for_unknown_session(client, auth):
    response = client.patch(
        "/sessions/nonexistent-id/rename",
        json={"title": "New Name"},
        headers=auth
    )
    assert response.status_code == 404


def test_rename_session_rejects_empty_title(client, auth):
    session_id = _seed_session([("user", "Hello")])
    response = client.patch(
        f"/sessions/{session_id}/rename",
        json={"title": "   "},
        headers=auth
    )
    assert response.status_code == 422


# ── DELETE /history/{session_id} ─────────────────────────────────────────────

def test_delete_session_removes_history(client, auth):
    session_id = _seed_session([("user", "Hello")])
    client.delete(f"/history/{session_id}", headers=auth)
    response = client.get(f"/history/{session_id}", headers=auth)
    assert response.status_code == 404


def test_delete_session_returns_200(client, auth):
    session_id = _seed_session([("user", "Hello")])
    response = client.delete(f"/history/{session_id}", headers=auth)
    assert response.status_code == 200


def test_delete_session_returns_404_for_unknown_session(client, auth):
    response = client.delete("/history/nonexistent-id", headers=auth)
    assert response.status_code == 404


def test_delete_removes_session_from_list(client, auth):
    session_id = _seed_session([("user", "Hello")])
    client.delete(f"/history/{session_id}", headers=auth)
    sessions = client.get("/sessions", headers=auth).json()["sessions"]
    ids = [s["session_id"] for s in sessions]
    assert session_id not in ids

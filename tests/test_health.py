"""
Tests for GET /health endpoint.
This is a public endpoint — no API key required.
"""


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status(client):
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_returns_version(client):
    response = client.get("/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "1.0"


def test_health_requires_no_auth(client):
    """Health endpoint must be reachable without any API key."""
    response = client.get("/health")
    assert response.status_code != 401

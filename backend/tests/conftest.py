import pytest
from fastapi.testclient import TestClient
from api.main import app
import config as cfg

TEST_API_KEY = "test-secret-key"


@pytest.fixture(scope="session", autouse=True)
def patch_api_key():
    """Override API secret key for all tests so auth works without a real .env."""
    original = cfg.config.api_secret_key
    cfg.config.api_secret_key = TEST_API_KEY
    yield
    cfg.config.api_secret_key = original


@pytest.fixture(scope="session")
def client():
    """Shared FastAPI test client — starts the app once for the whole session."""
    return TestClient(app)


@pytest.fixture
def auth():
    """Auth headers using the test API key."""
    return {"X-API-Key": TEST_API_KEY}

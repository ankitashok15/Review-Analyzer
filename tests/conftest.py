import pytest
from fastapi.testclient import TestClient

from config.settings import get_settings
from src.api.main import app

TEST_ADMIN_KEY = "test-admin-key"


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_KEY)
    monkeypatch.setenv("REQUIRE_ADMIN_API_KEY", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-API-Key": TEST_ADMIN_KEY}

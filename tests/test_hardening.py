from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from config.settings import get_settings
from src.api.main import app
from src.security.rate_limit import reset_rate_limits_for_tests
from tests.conftest import TEST_ADMIN_KEY


@pytest.fixture
def hardened_client():
    get_settings.cache_clear()
    reset_rate_limits_for_tests()
    client = TestClient(app)
    yield client, {"X-API-Key": TEST_ADMIN_KEY}
    get_settings.cache_clear()
    reset_rate_limits_for_tests()


def test_sanitize_strips_control_chars():
    from src.security.sanitize import sanitize_query

    assert sanitize_query("hello\x00world") == "helloworld"


def test_admin_required_on_ingest(hardened_client):
    client, _ = hardened_client
    response = client.post("/api/v1/ingest", json={"source": "csv", "limit": 1})
    assert response.status_code == 401


@patch("src.api.routes.ingest.IngestionService")
def test_admin_ingest_with_key(mock_service_cls, hardened_client):
    mock_service_cls.return_value.run.return_value = type(
        "R",
        (),
        {
            "inserted": 1,
            "skipped": 0,
            "rejected": 0,
            "duplicates": 0,
            "failed": 0,
            "errors": [],
        },
    )()
    client, headers = hardened_client
    response = client.post(
        "/api/v1/ingest",
        json={"source": "csv", "limit": 1},
        headers=headers,
    )
    assert response.status_code == 200


def test_admin_required_on_export(hardened_client):
    client, _ = hardened_client
    import uuid

    response = client.post(
        "/api/v1/export",
        json={"format": "json", "review_ids": [str(uuid.uuid4())]},
    )
    assert response.status_code == 401


def test_health_detailed(hardened_client):
    client, _ = hardened_client
    response = client.get("/health?detailed=true")
    assert response.status_code == 200
    data = response.json()
    assert "redis" in data
    assert "celery" in data


def test_metrics_endpoint(hardened_client):
    client, _ = hardened_client
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "counters" in response.json()


@patch("src.api.routes.search.SemanticSearchService")
def test_search_sanitizes_query(mock_service_cls, hardened_client):
    mock_service_cls.return_value.search.return_value = []
    client, _ = hardened_client
    response = client.post("/api/v1/search", json={"query": "  hello   world  ", "top_k": 3})
    assert response.status_code == 200
    assert response.json()["query"] == "hello world"


def test_job_not_found(hardened_client):
    client, _ = hardened_client
    response = client.get("/api/v1/jobs/nonexistent-job-id")
    assert response.status_code == 404


def test_request_id_header(hardened_client):
    client, _ = hardened_client
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

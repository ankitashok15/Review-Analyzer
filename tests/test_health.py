def test_health_endpoint_returns_expected_shape(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "review-discovery-engine"
    assert data["status"] in ("ok", "degraded")
    assert data["db"] in ("connected", "disconnected")

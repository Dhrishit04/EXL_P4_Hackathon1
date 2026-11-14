"""Check the live HTTP contract and error envelope."""


def test_health_and_errors(client, requests):
    """Expose shared liveness, schema, file and route error formats."""
    assert client.get("/health").json() == {"status": "ok", "service": "validation_lab", "version": "0.1.0"}
    response = client.post("/validate", json={})
    assert response.status_code == 422 and response.json()["error"]["code"] == "INVALID_REQUEST"
    request = requests["validate"]
    request["data"]["dev_path"] = "missing.csv"
    response = client.post("/validate", json=request)
    assert response.status_code == 404 and response.json()["error"]["code"] == "FILE_NOT_FOUND"
    assert client.get("/unknown").json()["error"]["code"] == "HTTP_ERROR"

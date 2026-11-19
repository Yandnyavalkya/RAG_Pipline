SECRET_MARKERS = (
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
    "mongodb_uri",
    "jwt",
    "credential",
)


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["api_version"] == "v1"


def test_health_does_not_expose_secrets(client):
    response = client.get("/health")
    body = response.text.lower()

    for marker in SECRET_MARKERS:
        assert marker not in body


def test_openapi_docs_are_available(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_api_v1_prefix_is_mounted(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 404

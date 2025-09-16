from fastapi.testclient import TestClient


def test_login_missing_user(client: TestClient):
    resp = client.post("/api/v2/auth/login", data={"username": "nouser@example.com", "password": "wrong"})
    assert resp.status_code in (400, 401)


def test_refresh_invalid_token(client: TestClient):
    resp = client.post("/api/v2/auth/refresh", json={"refresh_token": "invalid"})
    assert resp.status_code in (401, 403)



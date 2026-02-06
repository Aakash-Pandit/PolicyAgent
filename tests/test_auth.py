import pytest

from auth.jwt import create_access_token, decode_access_token
from auth.passwords import hash_password, verify_password


def test_create_and_decode_token():
    token = create_access_token({"sub": "123", "user_type": "ADMIN"})
    payload = decode_access_token(token)
    assert payload["sub"] == "123"
    assert payload["user_type"] == "ADMIN"


def test_decode_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_access_token("not-a-real-token")


def test_hash_and_verify_password():
    hashed = hash_password("my-pass-123")
    assert verify_password("my-pass-123", hashed) is True
    assert verify_password("wrong-pass", hashed) is False


def test_login_success(client, create_user):
    create_user(username="admin", password="secret", email="admin@example.com")
    response = client.post(
        "/login",
        json={"username": "admin", "password": "secret"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_login_invalid_credentials(client):
    response = client.post(
        "/login",
        json={"username": "missing", "password": "nope"},
    )
    assert response.status_code == 401


def test_protected_endpoint_requires_auth(client):
    response = client.get("/patients")
    assert response.status_code == 401


def test_protected_endpoint_accepts_valid_token(client, create_user, auth_headers):
    user = create_user(username="pat", email="pat@example.com")
    response = client.get("/patients", headers=auth_headers(user))
    assert response.status_code == 200

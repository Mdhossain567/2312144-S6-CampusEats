"""Automated test suite for Authentication, Tokens, Sessions, Lockout, and Ban checks."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.clock import utc_now
from app.config import JWT_SECRET
from app.users.models import AppUser


def test_register_and_login(client: TestClient):
    # 1. Register
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "test@campuseats.com", "password": "Password123"},
    )
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "test@campuseats.com"
    assert user_data["role"] == "customer"
    assert user_data["is_banned"] is False

    # 2. Duplicate registration rejected
    dup_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User 2", "email": "test@campuseats.com", "password": "Password123"},
    )
    assert dup_res.status_code == 409

    # 3. Login success
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "test@campuseats.com", "password": "Password123"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["expires_in"] == 900  # 15 minutes = 900 seconds
    assert "campuseats_refresh" in login_res.cookies


def test_invalid_password(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "invalid_pw@campuseats.com", "password": "Password123"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "invalid_pw@campuseats.com", "password": "WrongPassword123"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_brute_force_lockout(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Lockout User", "email": "lockout@campuseats.com", "password": "Password123"},
    )

    # 5 consecutive wrong password attempts
    for _ in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "lockout@campuseats.com", "password": "WrongPassword123"},
        )
        assert res.status_code == 401

    # 6th attempt should be blocked by rate limit / lockout with 429
    locked_res = client.post(
        "/api/v1/auth/login",
        json={"email": "lockout@campuseats.com", "password": "Password123"},
    )
    assert locked_res.status_code == 429
    assert "Too many failed attempts" in locked_res.json()["detail"]


def test_token_rejection_missing(client: TestClient):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["detail"] == "Not authenticated"


def test_token_rejection_tampered(client: TestClient):
    headers = {"Authorization": "Bearer tampered.fake.jwt-token-string"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    assert "Invalid or expired token" in res.json()["detail"]


def test_token_rejection_expired(client: TestClient, session: Session):
    # Register and create a user
    client.post(
        "/api/v1/auth/register",
        json={"name": "Expired Test", "email": "expired@campuseats.com", "password": "Password123"},
    )
    user = session.exec(select(AppUser).where(AppUser.email == "expired@campuseats.com")).first()

    # Craft an expired token (expired 10 minutes ago)
    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    payload = {"sub": str(user.id), "role": user.role, "iat": past - timedelta(minutes=15), "exp": past}
    expired_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    headers = {"Authorization": f"Bearer {expired_token}"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    assert "Invalid or expired token" in res.json()["detail"]


def test_banned_user_immediate_rejection(client: TestClient, session: Session):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Ban Test", "email": "tobeban@campuseats.com", "password": "Password123"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "tobeban@campuseats.com", "password": "Password123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify user can access /me currently
    res_ok = client.get("/api/v1/auth/me", headers=headers)
    assert res_ok.status_code == 200

    # Admin bans the user directly in database
    user = session.exec(select(AppUser).where(AppUser.email == "tobeban@campuseats.com")).first()
    user.is_banned = True
    user.ban_reason = "Test ban"
    session.add(user)
    session.commit()

    # On the very next request, access must be denied with 403 Forbidden
    res_banned = client.get("/api/v1/auth/me", headers=headers)
    assert res_banned.status_code == 403
    assert "Account is banned" in res_banned.json()["detail"]


def test_refresh_token_rotation(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Refresh User", "email": "refresh@campuseats.com", "password": "Password123"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@campuseats.com", "password": "Password123"},
    )
    old_cookie = login_res.cookies.get("campuseats_refresh")
    assert old_cookie is not None

    # Call /refresh with cookie
    ref_res = client.post("/api/v1/auth/refresh")
    assert ref_res.status_code == 200
    new_data = ref_res.json()
    assert "access_token" in new_data

    # Cookie rotated to new token
    new_cookie = ref_res.cookies.get("campuseats_refresh")
    assert new_cookie is not None
    assert new_cookie != old_cookie


def test_change_password(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Password User", "email": "pw_change@campuseats.com", "password": "Password123"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "pw_change@campuseats.com", "password": "Password123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Wrong current password fails
    bad_change = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongPassword123", "new_password": "NewPassword456"},
        headers=headers,
    )
    assert bad_change.status_code == 401

    # Correct current password succeeds
    good_change = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Password123", "new_password": "NewPassword456"},
        headers=headers,
    )
    assert good_change.status_code == 204

    # Old password no longer works
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pw_change@campuseats.com", "password": "Password123"},
    )
    assert old_login.status_code == 401

    # New password logs in successfully
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pw_change@campuseats.com", "password": "NewPassword456"},
    )
    assert new_login.status_code == 200

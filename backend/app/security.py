"""Password hashing (Argon2id + server-side pepper) and access tokens (JWT)."""
import hashlib
import hmac
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.clock import utc_now
from app.config import ACCESS_TOKEN_MINUTES, JWT_SECRET, PASSWORD_PEPPER

ALGORITHM = "HS256"

_hasher = PasswordHasher()


def _pepper(password: str) -> str:
    """HMAC-SHA256 the plain password with the server-side pepper.

    The pepper is never stored in the database. An attacker who dumps the hash
    table still cannot run offline dictionary attacks without the pepper value.
    """
    return hmac.new(
        PASSWORD_PEPPER.encode(), password.encode(), hashlib.sha256
    ).hexdigest()


# Checked when the email is unknown so a missing account takes as long as a
# real password check — an attacker cannot distinguish the two cases by timing.
DUMMY_HASH = _hasher.hash(_pepper("campuseats-not-a-real-password"))


def hash_password(password: str) -> str:
    """Return a salted Argon2id hash of pepper(password). The plain password is never stored."""
    return _hasher.hash(_pepper(password))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, _pepper(password))
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    """Return (signed_token, lifetime_in_seconds). Lifetime is <= 15 minutes."""
    lifetime = timedelta(minutes=ACCESS_TOKEN_MINUTES)
    now = utc_now()
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + lifetime}
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> dict | None:
    """Return the token's claims, or None if it is invalid or expired."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None

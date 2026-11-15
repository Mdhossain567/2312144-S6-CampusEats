"""Password hashing (Argon2id) and access tokens (JWT)."""
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.clock import utc_now
from app.config import ACCESS_TOKEN_MINUTES, JWT_SECRET

ALGORITHM = "HS256"

_hasher = PasswordHasher()

# Checked when the email is unknown, so a missing account takes as long as a wrong
# password and an attacker cannot tell the two cases apart by timing.
DUMMY_HASH = _hasher.hash("campuseats-not-a-real-password")


def hash_password(password: str) -> str:
    """Return a salted Argon2id hash. The plain password is never stored."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    """Return the signed token and its lifetime in seconds."""
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
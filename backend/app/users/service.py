"""Business rules for registering and logging in."""
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.clock import as_utc, utc_now
from app.security import DUMMY_HASH, hash_password, verify_password
from app.users import repository
from app.users.models import AppUser
from app.users.schemas import UserRegister

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15


def _email_taken() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "Email is already registered")


def _invalid_login() -> HTTPException:
    # One message for a wrong email and a wrong password, so nobody can find out
    # which emails have an account.
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


def register(session: Session, data: UserRegister) -> AppUser:
    if repository.get_by_email(session, data.email):
        raise _email_taken()

    # The role is never taken from the request: everyone starts as a customer.
    user = AppUser(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="customer",
    )
    try:
        return repository.save(session, user)
    except IntegrityError:
        session.rollback()
        raise _email_taken()


def authenticate(session: Session, email: str, password: str) -> AppUser:
    user = repository.get_by_email(session, email)
    if user is None:
        verify_password(password, DUMMY_HASH)  # same work as a real check
        raise _invalid_login()

    now = utc_now()
    if user.locked_until is not None and as_utc(user.locked_until) > now:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed attempts. Try again later.",
        )

    if not verify_password(password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
            user.failed_logins = 0
        repository.save(session, user)
        raise _invalid_login()

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated")

    user.failed_logins = 0
    user.locked_until = None
    user.last_login_at = now
    return repository.save(session, user)
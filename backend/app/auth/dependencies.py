"""Who is calling (authentication) and what they may do (authorization)."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import SessionDep
from app.security import decode_access_token
from app.users import repository
from app.users.models import AppUser

bearer = HTTPBearer(auto_error=False)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: SessionDep,
) -> AppUser:
    if credentials is None:
        raise _unauthorized("Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise _unauthorized("Invalid or expired token")

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise _unauthorized("Invalid or expired token")

    # The role and the active flag are read from the database on every request,
    # so a change by an admin applies immediately, whatever the token says.
    user = repository.get(session, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Invalid or expired token")
    return user


CurrentUser = Annotated[AppUser, Depends(get_current_user)]


def require_roles(*allowed_roles: str):
    """Allow only users whose role is in allowed_roles (403 for everyone else)."""

    def check(user: CurrentUser) -> AppUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "You do not have permission to do this"
            )
        return user

    return check
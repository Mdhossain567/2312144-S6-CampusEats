"""Who is calling (authentication) and what they may do (authorization)."""
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import SessionDep
from app.security import decode_access_token
from app.users import repository
from app.users.models import AppUser

bearer = HTTPBearer(auto_error=False)

REFRESH_COOKIE = "campuseats_refresh"


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

    # Role, active flag, and ban status are read from the database on every
    # request so an admin change applies immediately, whatever the token says.
    user = repository.get(session, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Invalid or expired token")

    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is banned")

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


def get_refresh_token_from_cookie(request: Request) -> str | None:
    """Read the raw refresh token from the httpOnly cookie."""
    return request.cookies.get(REFRESH_COOKIE)

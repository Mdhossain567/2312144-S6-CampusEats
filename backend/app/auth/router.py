"""HTTP endpoints for accounts under /api/v1/auth (JSON)."""
import os

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.auth.dependencies import (
    CurrentUser,
    REFRESH_COOKIE,
    get_refresh_token_from_cookie,
)
from app.clock import as_utc, utc_now
from app.database import SessionDep
from app.security import create_access_token
from app.users import repository, service
from app.users import session_repository as sess_repo
from app.users.schemas import (
    PasswordChange,
    ProfileUpdate,
    SessionRead,
    TokenResponse,
    UserLogin,
    UserRead,
    UserRegister,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Refresh tokens are Secure on Vercel (HTTPS); plain on localhost (HTTP dev).
_IS_PROD = bool(os.getenv("VERCEL"))


def _set_refresh_cookie(response: Response, raw_token: str, max_age: int) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=_IS_PROD,
        max_age=max_age,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE,
        path="/api/v1/auth",
        httponly=True,
        samesite="lax",
        secure=_IS_PROD,
    )


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, session: SessionDep):
    return service.register(session, data)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, request: Request, response: Response, session: SessionDep):
    user = service.authenticate(session, data.email, data.password)
    access_token, expires_in = create_access_token(user.id, user.role)

    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    _, raw_refresh = sess_repo.create_session(session, user.id, user_agent, ip_address)

    from app.config import REFRESH_TOKEN_DAYS
    _set_refresh_cookie(response, raw_refresh, max_age=REFRESH_TOKEN_DAYS * 86400)

    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, session: SessionDep):
    """Issue a new access token and rotate the refresh token cookie."""
    raw_token = get_refresh_token_from_cookie(request)
    if not raw_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")

    db_session = sess_repo.get_by_token(session, raw_token)
    if db_session is None or db_session.revoked:
        _clear_refresh_cookie(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked session")

    if as_utc(db_session.expires_at) < utc_now():
        _clear_refresh_cookie(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    user = repository.get(session, db_session.user_id)
    if user is None or not user.is_active:
        _clear_refresh_cookie(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    if user.is_banned:
        _clear_refresh_cookie(response)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is banned")

    # Rotate: invalidate the old token hash and issue a new one.
    _, new_raw = sess_repo.rotate(session, db_session)
    access_token, expires_in = create_access_token(user.id, user.role)

    from app.config import REFRESH_TOKEN_DAYS
    _set_refresh_cookie(response, new_raw, max_age=REFRESH_TOKEN_DAYS * 86400)

    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, session: SessionDep):
    """Revoke the server-side session and clear the cookie."""
    raw_token = get_refresh_token_from_cookie(request)
    if raw_token:
        db_session = sess_repo.get_by_token(session, raw_token)
        if db_session and not db_session.revoked:
            sess_repo.revoke(session, db_session)
    _clear_refresh_cookie(response)


# ---------------------------------------------------------------------------
# Protected endpoints
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser):
    return user


@router.patch("/profile", response_model=UserRead)
def update_profile(data: ProfileUpdate, user: CurrentUser, session: SessionDep):
    return service.update_profile(session, user, data)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChange,
    request: Request,
    response: Response,
    user: CurrentUser,
    session: SessionDep,
):
    """Change the user's password, then revoke all other sessions."""
    service.change_password(session, user, data)

    # Revoke every session except the current one so other devices are logged out.
    raw_token = get_refresh_token_from_cookie(request)
    current_session_id: int | None = None
    if raw_token:
        db_session = sess_repo.get_by_token(session, raw_token)
        if db_session:
            current_session_id = db_session.id

    if current_session_id is not None:
        sess_repo.revoke_all_except(session, user.id, current_session_id)
    else:
        # No cookie — revoke everything
        for s in sess_repo.list_active(session, user.id):
            sess_repo.revoke(session, s)


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(request: Request, user: CurrentUser, session: SessionDep):
    """Return all active sessions for the current user, flagging the current one."""
    raw_token = get_refresh_token_from_cookie(request)
    current_session_id: int | None = None
    if raw_token:
        db_session = sess_repo.get_by_token(session, raw_token)
        if db_session:
            current_session_id = db_session.id

    active = sess_repo.list_active(session, user.id)
    return [
        SessionRead(
            id=s.id,
            user_agent=s.user_agent,
            ip_address=s.ip_address,
            created_at=s.created_at,
            expires_at=s.expires_at,
            is_current=(s.id == current_session_id),
        )
        for s in active
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(session_id: int, user: CurrentUser, session: SessionDep):
    """Revoke a specific session owned by the current user."""
    found = sess_repo.revoke_by_id(session, session_id, user.id)
    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

"""HTTP endpoints for accounts under /api/v1/auth (JSON)."""
from fastapi import APIRouter, status

from app.auth.dependencies import CurrentUser
from app.database import SessionDep
from app.security import create_access_token
from app.users import service
from app.users.schemas import TokenResponse, UserLogin, UserRead, UserRegister

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, session: SessionDep):
    return service.register(session, data)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, session: SessionDep):
    user = service.authenticate(session, data.email, data.password)
    token, expires_in = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser):
    return user
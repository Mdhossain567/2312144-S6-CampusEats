"""Pytest test configuration and fixtures."""
import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Configure test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-jwt-secret-key-for-pytest-execution"
os.environ["PASSWORD_PEPPER"] = "test-pepper-secret-for-pytest"
os.environ["ACCESS_TOKEN_MINUTES"] = "15"

# Register all SQLModel tables
import app.audit.models  # noqa: F401
import app.groups.models  # noqa: F401
import app.menu_items.models  # noqa: F401
import app.orders.models  # noqa: F401
import app.users.models  # noqa: F401
import app.users.session_model  # noqa: F401

from app.database import get_session
from main import app

# In-memory SQLite engine with StaticPool so all connections share the same memory database
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def setup_database():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture() -> Generator[TestClient, None, None]:
    def get_session_override() -> Generator[Session, None, None]:
        with Session(test_engine) as s:
            yield s

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

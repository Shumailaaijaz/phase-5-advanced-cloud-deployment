"""Test fixtures for integration tests."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
import os

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_DAYS"] = "7"
os.environ["VITE_NEON_AUTH_URL"] = "http://localhost:3000"
os.environ["BETTER_AUTH_SECRET"] = "test-better-auth-secret"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine with SQLite in-memory."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(test_engine):
    """Create a test client with mocked database session."""
    from main import app
    from database.session import get_session

    def get_test_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Sample user IDs for isolation tests
TEST_USER_A = "user-a-12345"
TEST_USER_B = "user-b-67890"
TEST_USER_C = "user-c-11111"


@pytest.fixture
def user_a_id():
    """User A ID for isolation tests."""
    return TEST_USER_A


@pytest.fixture
def user_b_id():
    """User B ID for isolation tests."""
    return TEST_USER_B


@pytest.fixture
def mock_auth_user_a():
    """Mock authentication for User A."""
    with patch("api.deps.get_current_user") as mock:
        mock.return_value = {"user_id": TEST_USER_A}
        yield mock


@pytest.fixture
def mock_auth_user_b():
    """Mock authentication for User B."""
    with patch("api.deps.get_current_user") as mock:
        mock.return_value = {"user_id": TEST_USER_B}
        yield mock


@pytest.fixture
def auth_headers_user_a():
    """Auth headers for User A (mock JWT)."""
    return {"Authorization": "Bearer mock-token-user-a"}


@pytest.fixture
def auth_headers_user_b():
    """Auth headers for User B (mock JWT)."""
    return {"Authorization": "Bearer mock-token-user-b"}

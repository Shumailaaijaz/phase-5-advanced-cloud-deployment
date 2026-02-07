"""MCP Test Fixtures

Provides isolated test database and sample data for MCP tool tests.
"""

import pytest
from datetime import datetime
from typing import Generator, Callable

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from backend.models.user import User, Task


@pytest.fixture(name="engine")
def engine_fixture():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine) -> Generator[Session, None, None]:
    """Create fresh session for each test."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="get_session")
def get_session_fixture(engine) -> Callable[[], Session]:
    """Factory fixture for creating sessions."""
    def _get_session() -> Session:
        return Session(engine)
    return _get_session


@pytest.fixture(name="user_a")
def user_a_fixture(session: Session) -> User:
    """Create test user A."""
    user = User(
        email="user_a@test.com",
        full_name="User A",
        hashed_password="hashed_password_a",
        created_at=datetime.utcnow(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="user_b")
def user_b_fixture(session: Session) -> User:
    """Create test user B for isolation tests."""
    user = User(
        email="user_b@test.com",
        full_name="User B",
        hashed_password="hashed_password_b",
        created_at=datetime.utcnow(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="task_for_user_a")
def task_for_user_a_fixture(session: Session, user_a: User) -> Task:
    """Create a sample task for user A."""
    task = Task(
        user_id=user_a.id,
        title="User A's task",
        description="A sample task",
        priority="Medium",
        completed=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture(name="task_for_user_b")
def task_for_user_b_fixture(session: Session, user_b: User) -> Task:
    """Create a sample task for user B."""
    task = Task(
        user_id=user_b.id,
        title="User B's task",
        description="Another sample task",
        priority="High",
        completed=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture(name="completed_task_for_user_a")
def completed_task_fixture(session: Session, user_a: User) -> Task:
    """Create a completed task for user A."""
    task = Task(
        user_id=user_a.id,
        title="Completed task",
        description="Already done",
        priority="Low",
        completed=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

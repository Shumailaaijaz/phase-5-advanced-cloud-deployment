from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlmodel import Session
from typing import Generator
import os
from core.config import settings


# Create the database engine
# Use NullPool for serverless environments (Vercel) - no persistent connections
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Serverless-friendly: no connection pooling
    pool_pre_ping=True,
)


def get_session() -> Generator[Session, None, None]:
    """
    Get a database session from the engine.
    This function is meant to be used as a FastAPI dependency.
    """
    with Session(engine) as session:
        yield session
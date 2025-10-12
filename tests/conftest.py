"""
Root test fixtures and configuration.

This module provides shared fixtures for database sessions, test clients,
and other common testing utilities.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.main import app

# Test database URL - use separate test database
TEST_DATABASE_URL = settings.DATABASE_URL.replace('/studio_db', '/studio_test_db')


@pytest.fixture(scope='session')
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create event loop for async tests.

    This fixture is scoped to the session to allow async fixtures
    with session scope.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create test database engine.

    This engine is shared across all tests in the session for performance.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope='session')
async def setup_database(test_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """
    Setup test database tables.

    Creates all tables before tests and drops them after.
    This fixture runs once per test session.
    """
    async with test_engine.begin() as conn:
        # Import all models to register them with SQLModel
        from app.catalog import models as catalog_models  # noqa: F401
        from app.clients import models as client_models  # noqa: F401
        from app.sessions import models as session_models  # noqa: F401
        from app.users import models as user_models  # noqa: F401

        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Drop all tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(
    test_engine: AsyncEngine, setup_database: None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for each test with automatic rollback.

    Each test gets a fresh session that is rolled back after the test
    completes, ensuring test isolation.
    """
    # Create session factory
    async_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session_maker() as session:
        # Begin nested transaction
        async with session.begin():
            yield session
            # Rollback automatically happens when exiting context


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with dependency overrides.

    The database session dependency is overridden to use the test session,
    ensuring all API calls use the test database.
    """
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Override dependency
    app.dependency_overrides[get_session] = override_get_session

    # Create async client
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def anyio_backend() -> str:
    """Configure anyio backend for async tests."""
    return 'asyncio'

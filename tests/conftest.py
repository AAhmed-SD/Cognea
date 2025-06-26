import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

from main import app
from models.database import Base
from services.auth import create_access_token

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for testing
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async session factory
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_setup():
    """Create test database tables before tests and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session(test_db_setup) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for synchronous testing."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def test_user_token() -> str:
    """Create a test user token."""
    return create_access_token({"sub": "test@example.com", "role": "user"})

@pytest.fixture(scope="function")
def test_admin_token() -> str:
    """Create a test admin token."""
    return create_access_token({"sub": "admin@example.com", "role": "admin"})

@pytest.fixture(scope="function")
def auth_headers(test_user_token) -> dict:
    """Create authorization headers with test user token."""
    return {"Authorization": f"Bearer {test_user_token}"}

@pytest.fixture(scope="function")
def admin_headers(test_admin_token) -> dict:
    """Create authorization headers with test admin token."""
    return {"Authorization": f"Bearer {test_admin_token}"}

@pytest.fixture(autouse=True, scope="function")
async def setup_test_environment():
    """Setup test environment variables and cleanup."""
    os.environ["TEST_ENV"] = "true"
    os.environ["DISABLE_RATE_LIMIT"] = "true"
    yield
    os.environ.pop("TEST_ENV", None)
    os.environ.pop("DISABLE_RATE_LIMIT", None) 
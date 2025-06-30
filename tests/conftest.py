import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import create_app
from services.supabase import get_supabase_client
from services.auth import create_access_token


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def supabase_client():
    """Get Supabase client for testing."""
    return get_supabase_client()


@pytest_asyncio.fixture(scope="function")
async def db_session(supabase_client):
    """Create a mock database session for compatibility."""

    # Return a mock object that has the same interface as SQLAlchemy session
    class MockSession:
        def __init__(self, supabase_client):
            self.supabase = supabase_client
            self.added_items = []

        def add(self, item):
            self.added_items.append(item)

        def add_all(self, items):
            self.added_items.extend(items)

        async def commit(self):
            # For now, just clear the items since we're using Supabase directly
            self.added_items.clear()

        async def close(self):
            pass

    session = MockSession(supabase_client)
    yield session
    await session.close()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for testing."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for synchronous testing."""
    app = create_app()
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


@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_test_environment():
    """Setup test environment variables and cleanup."""
    os.environ["TEST_ENV"] = "true"
    os.environ["DISABLE_RATE_LIMIT"] = "true"
    yield
    os.environ.pop("TEST_ENV", None)
    os.environ.pop("DISABLE_RATE_LIMIT", None)

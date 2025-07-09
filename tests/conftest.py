import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

import types
from unittest.mock import MagicMock

# Provide a minimal stub for 'distutils' to satisfy legacy packages (e.g., aioredis) on Python 3.12+
if 'distutils' not in sys.modules:
    distutils_stub = types.ModuleType('distutils')
    version_stub = types.ModuleType('distutils.version')

    class _StrictVersion(str):
        pass

    version_stub.StrictVersion = _StrictVersion  # type: ignore[attr-defined]
    distutils_stub.version = version_stub  # type: ignore[attr-defined]
    sys.modules['distutils'] = distutils_stub
    sys.modules['distutils.version'] = version_stub

# Provide a minimal stub for 'redis.asyncio' if the redis package without asyncio support is installed.
if 'redis.asyncio' not in sys.modules:
    redis_asyncio_stub = types.ModuleType('redis.asyncio')

    class _DummyRedisClient:  # Basic stub mimicking the Redis asyncio interface
        async def get(self, *_, **__):
            return None

        async def set(self, *_, **__):
            pass

        async def incr(self, *_, **__):
            return 1

        async def configure(self, *_, **__):
            pass

    redis_asyncio_stub.Redis = _DummyRedisClient  # type: ignore[attr-defined]
    class _DummyConnectionPool:  # Simple placeholder
        def __init__(self, *_, **__):
            pass

        @classmethod
        def from_url(cls, *_, **__):
            return cls()

    redis_asyncio_stub.ConnectionPool = _DummyConnectionPool  # type: ignore[attr-defined]
    sys.modules['redis.asyncio'] = redis_asyncio_stub

# Provide a minimal stub for 'prometheus_client' if missing
if 'prometheus_client' not in sys.modules:
    prom_stub = types.ModuleType('prometheus_client')

    class _DummyMetric:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *_, **__):
            return self

        def inc(self, *_, **__):
            pass

        def observe(self, *_, **__):
            pass

    prom_stub.Counter = _DummyMetric  # type: ignore[attr-defined]
    prom_stub.Gauge = _DummyMetric  # type: ignore[attr-defined]
    prom_stub.Histogram = _DummyMetric  # type: ignore[attr-defined]
    prom_stub.generate_latest = lambda *args, **kwargs: b''  # type: ignore[attr-defined]

    sys.modules['prometheus_client'] = prom_stub

# Patch 'stripe' module with minimal stubs if critical submodules are missing.
try:
    import stripe as _stripe  # type: ignore

    if getattr(_stripe, 'checkout', None) is None:
        class _DummyCheckout:
            class Session:  # type: ignore[override]
                @staticmethod
                def create(*args, **kwargs):
                    class _DummySession:
                        id = 'cs_test_123'
                        customer = 'cus_test_123'
                        metadata = kwargs.get('metadata', {})
                    return _DummySession()
        _stripe.checkout = _DummyCheckout()  # type: ignore[attr-defined]

    if getattr(_stripe, 'billing_portal', None) is None:
        class _DummyBillingPortal:
            class Session:  # type: ignore[override]
                @staticmethod
                def create(*args, **kwargs):
                    class _DummyBP:
                        id = 'bp_test_123'
                    return _DummyBP()
        _stripe.billing_portal = _DummyBillingPortal()  # type: ignore[attr-defined]

    if not hasattr(_stripe, 'Subscription'):
        class _DummySubscription:  # type: ignore[override]
            id = 'sub_test_123'
            status = 'active'
            current_period_end = 0
            cancel_at_period_end = False

            @staticmethod
            def retrieve(*args, **kwargs):
                return _DummySubscription()
        _stripe.Subscription = _DummySubscription  # type: ignore[attr-defined]

    if not hasattr(_stripe, 'Invoice'):
        class _DummyInvoice:  # type: ignore[override]
            subscription = 'sub_test_123'
        _stripe.Invoice = _DummyInvoice  # type: ignore[attr-defined]

    if not hasattr(_stripe, 'Webhook'):
        class _DummyWebhook:  # type: ignore[override]
            @staticmethod
            def construct_event(payload, sig_header, secret):
                class _DummyEvent:
                    type = 'dummy.event'
                    data = type('obj', (), {'object': {}})  # simple placeholder
                return _DummyEvent()
        _stripe.Webhook = _DummyWebhook  # type: ignore[attr-defined]
except ImportError:
    pass

# Provide a minimal stub for 'aioredis' to avoid runtime import issues with Python 3.12+ where the official package may be incompatible.
if 'aioredis' not in sys.modules:
    aioredis_stub = types.ModuleType('aioredis')

    async def _create_redis_pool(*args, **kwargs):
        class _DummyRedisPool:  # Simple no-op async context manager
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, *_, **__):
                return None

            async def set(self, *_, **__):
                pass

        return _DummyRedisPool()

    aioredis_stub.create_redis_pool = _create_redis_pool  # type: ignore[attr-defined]
    sys.modules['aioredis'] = aioredis_stub

# Ensure required Supabase environment variables are set for the test environment BEFORE any application modules are imported.
os.environ.setdefault("SUPABASE_URL", "http://localhost/test-supabase")
os.environ.setdefault("SUPABASE_ANON_KEY", "test_anon_key")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import create_app
from services.auth import create_access_token
from services.supabase import get_supabase_client

# Replace Supabase client with a lightweight in-memory stub to prevent network calls during tests.
class _DummySupabase:
    def __init__(self):
        self.data = []

    # Chainable query methods
    def table(self, *_, **__):
        return self

    def select(self, *_, **__):
        return self

    def eq(self, *_, **__):
        return self

    def limit(self, *_, **__):
        return self

    def insert(self, *_, **__):
        return self

    def update(self, *_, **__):
        return self

    def execute(self):
        class _Result:
            data = []
        return _Result()

# Patch services.supabase.get_supabase_client to return the dummy instance
import importlib
supabase_module = importlib.import_module('services.supabase')
_dummy_supabase_instance = _DummySupabase()
supabase_module.supabase_client = _dummy_supabase_instance  # type: ignore[attr-defined]
supabase_module.get_supabase_client = lambda: _dummy_supabase_instance  # type: ignore[attr-defined]

# Patch services.redis_client.get_redis_client to prevent real Redis connections
try:
    redis_client_module = importlib.import_module('services.redis_client')

    class _DummyRedisWrapper:
        async def safe_call(self, *_, **__):
            # Simply call the target function synchronously
            fn = _[1] if len(_) > 1 else None  # extract if provided as positional
            if callable(fn):
                return fn()
            return None

    redis_client_module.get_redis_client = lambda: _DummyRedisWrapper()  # type: ignore[attr-defined]
except ModuleNotFoundError:
    pass


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

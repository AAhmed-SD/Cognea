import asyncio
from types import SimpleNamespace

import pytest

from services.redis_cache import EnhancedRedisCache


class _InMemoryRedis:
    """A minimal async Redis-like client for testing."""

    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key):  # noqa: D401
        return self.store.get(key)

    async def setex(self, key, ttl, value):  # noqa: D401
        # Ignore ttl for simplicity
        self.store[key] = value
        return True

    async def delete(self, key):  # noqa: D401
        return 1 if self.store.pop(key, None) is not None else 0

    async def keys(self, pattern):  # noqa: D401
        # naive pattern handling: only '*' wildcard
        if pattern == "*":
            return list(self.store.keys())
        return [k for k in self.store if pattern in k]

    async def mget(self, keys):  # noqa: D401
        return [self.store.get(k) for k in keys]

    async def pipeline(self):  # noqa: D401
        class _Pipe:
            def __init__(self, outer):
                self.outer = outer
                self.cmds = []

            def setex(self, k, ttl, v):
                self.cmds.append((k, v))

            async def execute(self):
                for k, v in self.cmds:
                    self.outer.store[k] = v
        pipe = _Pipe(self)
        # context mgr support
        class _CM:  # noqa: D401
            async def __aenter__(self):
                return pipe
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        return _CM()

    async def ping(self):  # noqa: D401
        return True

    async def close(self):
        pass


@pytest.fixture()
def cache():  # noqa: D401
    c = EnhancedRedisCache()
    c.client = _InMemoryRedis()  # type: ignore
    return c


@pytest.mark.asyncio
async def test_set_and_get_roundtrip(cache):  # noqa: D401
    assert await cache.set("user", {"name": "Bob"}, 60, 1)
    val = await cache.get("user", 1)
    assert val == {"name": "Bob"}
    metrics = cache.get_metrics()
    assert metrics["hits"] == 1 and metrics["misses"] == 0


@pytest.mark.asyncio
async def test_delete_and_clear(cache):  # noqa: D401
    await cache.set("demo", 123, 60, "x")
    assert await cache.delete("demo", "x") is True
    assert await cache.get("demo", "x") is None
    # Warmup two keys then clear pattern
    await cache.set("p", "a", 60, 1)
    await cache.set("p", "b", 60, 2)
    cleared = await cache.clear_pattern("p:*")
    assert cleared == 2


@pytest.mark.asyncio
async def test_get_or_set(cache):  # noqa: D401
    calls = {"count": 0}

    async def producer():
        calls["count"] += 1
        return "value"

    v1 = await cache.get_or_set("key", producer, 60, "a")
    v2 = await cache.get_or_set("key", producer, 60, "a")
    assert v1 == v2 == "value"
    assert calls["count"] == 1  # only produced once


def test_generate_key_length(cache):
    # create long kwargs to trigger hashing
    long_value = "x" * 300
    k = cache._generate_key("prefix", data=long_value)  # type: ignore
    assert len(k) < 250  # should be hashed and shortened
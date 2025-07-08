"""
Enhanced Redis Caching Service with Advanced Features
- Connection pooling
- Circuit breaker pattern
- Performance monitoring
- Automatic failover
- Cache warming
- Distributed locking
"""

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

logger = logging.getLogger(__name__)


class RedisCircuitBreaker:
    """Circuit breaker pattern for Redis operations"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        pass
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("Redis circuit breaker opened")

    def record_success(self):
        """Record a success and potentially close the circuit"""
        self.failure_count = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False

        return True  # HALF_OPEN


class EnhancedRedisCache:
    """Enhanced Redis caching service with advanced features"""

    def __init__(
        self,
        redis_url: str = None,
        max_connections: int = 20,
        connection_timeout: int = 5,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
    ):
        pass
        self.redis_url = redis_url or "redis://localhost:6379"
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval

        # Connection pool
        self.pool = None
        self.client = None

        # Circuit breaker
        self.circuit_breaker = RedisCircuitBreaker()

        # Performance metrics
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_operations": 0,
        }

        # Health check task
        self.health_check_task = None

        # Initialize connection
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize Redis connection with connection pool"""
        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                decode_responses=True,
            )

            self.client = redis.Redis(connection_pool=self.pool)
            logger.info("Enhanced Redis cache initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            self.client = None

    async def _health_check(self):
        """Periodic health check"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                if self.client:
                    await self.client.ping()
                    self.circuit_breaker.record_success()
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
                self.circuit_breaker.record_failure()

    async def start_health_check(self):
        """Start health check task"""
        if not self.health_check_task:
            self.health_check_task = asyncio.create_task(self._health_check())

    async def stop_health_check(self):
        """Stop health check task"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key with hash for long keys"""
        key_parts = [prefix]

        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))

        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (dict, list)):
                # Hash complex objects (non-security use)
                value_hash = hashlib.sha256(
                    json.dumps(value, sort_keys=True).encode()
                ).hexdigest()[:8]
                key_parts.append(f"{key}:{value_hash}")
            else:
                key_parts.append(f"{key}:{value}")

        # Create hash for long keys (non-security use)
        key_string = ":".join(key_parts)
        if len(key_string) > 250:  # Redis key length limit
            return f"{prefix}:{hashlib.sha256(key_string.encode()).hexdigest()}"

        return key_string

    async def get(self, prefix: str, *args, **kwargs) -> Any | None:
        """Get value from cache with circuit breaker"""
        if not self.client or not self.circuit_breaker.can_execute():
            return None

        try:
            key = self._generate_key(prefix, *args, **kwargs)
            value = await self.client.get(key)

            if value:
                self.metrics["hits"] += 1
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)

            self.metrics["misses"] += 1
            logger.debug(f"Cache miss for key: {key}")
            return None

        except Exception as e:
            self.metrics["errors"] += 1
            self.circuit_breaker.record_failure()
            logger.error(f"Cache get error: {e}")
            return None
        finally:
            self.metrics["total_operations"] += 1

    async def set(
        self,
        prefix: str,
        value: Any,
        ttl: int | timedelta = 3600,
        *args,
        **kwargs,
    ) -> bool:
        """Set value in cache with circuit breaker"""
        if not self.client or not self.circuit_breaker.can_execute():
            return False

        try:
            key = self._generate_key(prefix, *args, **kwargs)

            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            # Serialize value
            serialized_value = json.dumps(value, default=str)

            # Set in Redis
            await self.client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
            return True

        except Exception as e:
            self.metrics["errors"] += 1
            self.circuit_breaker.record_failure()
            logger.error(f"Cache set error: {e}")
            return False
        finally:
            self.metrics["total_operations"] += 1

    async def delete(self, prefix: str, *args, **kwargs) -> bool:
        """Delete value from cache"""
        if not self.client or not self.circuit_breaker.can_execute():
            return False

        try:
            key = self._generate_key(prefix, *args, **kwargs)
            result = await self.client.delete(key)
            logger.debug(f"Cache delete for key: {key}, result: {result}")
            return result > 0

        except Exception as e:
            self.metrics["errors"] += 1
            self.circuit_breaker.record_failure()
            logger.error(f"Cache delete error: {e}")
            return False
        finally:
            self.metrics["total_operations"] += 1

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.client or not self.circuit_breaker.can_execute():
            return 0

        try:
            keys = await self.client.keys(pattern)
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0

        except Exception as e:
            self.metrics["errors"] += 1
            self.circuit_breaker.record_failure()
            logger.error(f"Cache clear pattern error: {e}")
            return 0
        finally:
            self.metrics["total_operations"] += 1

    async def get_or_set(
        self,
        prefix: str,
        value_func: Callable,
        ttl: int | timedelta = 3600,
        *args,
        **kwargs,
    ) -> Any:
        """Get from cache or set if not exists"""
        # Try to get from cache first
        cached_value = await self.get(prefix, *args, **kwargs)
        if cached_value is not None:
            return cached_value

        # If not in cache, call function to get value
        try:
            if asyncio.iscoroutinefunction(value_func):
                value = await value_func()
            else:
                value = value_func()

            await self.set(prefix, value, ttl, *args, **kwargs)
            return value

        except Exception as e:
            logger.error(f"Cache get_or_set error: {e}")
            if asyncio.iscoroutinefunction(value_func):
                return await value_func()
            else:
                return value_func()

    async def mget(self, keys: list[str]) -> list[Any | None]:
        """Get multiple values from cache"""
        if not self.client or not self.circuit_breaker.can_execute():
            return [None] * len(keys)

        try:
            values = await self.client.mget(keys)
            result = []

            for i, value in enumerate(values):
                if value:
                    self.metrics["hits"] += 1
                    result.append(json.loads(value))
                else:
                    self.metrics["misses"] += 1
                    result.append(None)

            return result

        except Exception as e:
            self.metrics["errors"] += 1
            self.circuit_breaker.record_failure()
            logger.error(f"Cache mget error: {e}")
            return [None] * len(keys)
        finally:
            self.metrics["total_operations"] += 1

    async def mset(self, data: dict[str, Any], ttl: int | timedelta = 3600) -> bool:
        """Set multiple values in cache"""
        if not self.client or not self.circuit_breaker.can_execute():
            return False

        try:
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            # Serialize values
            serialized_data = {
                key: json.dumps(value, default=str) for key, value in data.items()
            }

            # Use pipeline for atomic operation
            async with self.client.pipeline() as pipe:
                for key, value in serialized_data.items():
                    pipe.setex(key, ttl, value)
                await pipe.execute()

            logger.debug(f"Cache mset for {len(data)} keys with TTL: {ttl}s")
            return True

        except Exception as e:
            self.metrics["errors"] += 1
            self.circuit_breaker.record_failure()
            logger.error(f"Cache mset error: {e}")
            return False
        finally:
            self.metrics["total_operations"] += 1

    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """Acquire a distributed lock"""
        if not self.client:
            return False

        try:
            lock_key = f"lock:{lock_name}"
            lock_value = str(time.time())

            # Try to acquire lock
            result = await self.client.set(lock_key, lock_value, ex=timeout, nx=True)

            return result is True

        except Exception as e:
            logger.error(f"Lock acquisition error: {e}")
            return False

    async def release_lock(self, lock_name: str) -> bool:
        """Release a distributed lock"""
        if not self.client:
            return False

        try:
            lock_key = f"lock:{lock_name}"
            result = await self.client.delete(lock_key)
            return result > 0

        except Exception as e:
            logger.error(f"Lock release error: {e}")
            return False

    async def warm_cache(self, warmup_data: dict[str, Any]) -> int:
        """Warm up cache with predefined data"""
        if not self.client:
            return 0

        try:
            count = 0
            for key, (value, ttl) in warmup_data.items():
                if await self.set("warmup", value, ttl, key):
                    count += 1

            logger.info(f"Cache warmed up with {count} entries")
            return count

        except Exception as e:
            logger.error(f"Cache warmup error: {e}")
            return 0

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics"""
        hit_rate = 0
        if self.metrics["total_operations"] > 0:
            hit_rate = self.metrics["hits"] / self.metrics["total_operations"]

        return {
            "hits": self.metrics["hits"],
            "misses": self.metrics["misses"],
            "errors": self.metrics["errors"],
            "total_operations": self.metrics["total_operations"],
            "hit_rate": hit_rate,
            "circuit_breaker_state": self.circuit_breaker.state,
            "connection_healthy": self.client is not None,
        }

    async def close(self):
        """Close Redis connection"""
        await self.stop_health_check()
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()


# Global enhanced cache instance
enhanced_cache = EnhancedRedisCache()


# Enhanced cache decorators
def enhanced_cached(prefix: str, ttl: int | timedelta = 3600):
    pass
    """Enhanced cache decorator for functions"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{prefix}:{func.__name__}"
            return await enhanced_cache.get_or_set(
                cache_key, lambda: func(*args, **kwargs), ttl, *args, **kwargs
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{prefix}:{func.__name__}"
            return enhanced_cache.get_or_set(
                cache_key, lambda: func(*args, **kwargs), ttl, *args, **kwargs
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def cache_with_lock(prefix: str, ttl: int | timedelta = 3600, lock_timeout: int = 10):
    pass
    """Cache decorator with distributed locking"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            lock_name = f"{prefix}:{func.__name__}"

            # Try to acquire lock
            if await enhanced_cache.acquire_lock(lock_name, lock_timeout):
                try:
                    cache_key = f"{prefix}:{func.__name__}"
                    return await enhanced_cache.get_or_set(
                        cache_key, lambda: func(*args, **kwargs), ttl, *args, **kwargs
                    )
                finally:
                    await enhanced_cache.release_lock(lock_name)
            else:
                # If lock acquisition fails, try to get from cache
                cache_key = f"{prefix}:{func.__name__}"
                return await enhanced_cache.get(cache_key, *args, **kwargs)

        return async_wrapper

    return decorator

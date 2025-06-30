import redis
import json
import hashlib
from typing import Any, Optional, Union
from datetime import timedelta
import logging
import os

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache service with Redis connection"""
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection"""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self.client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments"""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        # Create hash for long keys
        key_string = ":".join(key_parts)
        if len(key_string) > 250:  # Redis key length limit
            return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
        
        return key_string
    
    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            key = self._generate_key(prefix, *args, **kwargs)
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, prefix: str, value: Any, ttl: Union[int, timedelta] = 3600, *args, **kwargs) -> bool:
        """Set value in cache with TTL"""
        if not self.client:
            return False
        
        try:
            key = self._generate_key(prefix, *args, **kwargs)
            
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            # Serialize value
            serialized_value = json.dumps(value, default=str)
            
            # Set in Redis
            self.client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, prefix: str, *args, **kwargs) -> bool:
        """Delete value from cache"""
        if not self.client:
            return False
        
        try:
            key = self._generate_key(prefix, *args, **kwargs)
            result = self.client.delete(key)
            logger.debug(f"Cache delete for key: {key}, result: {result}")
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    def get_or_set(self, prefix: str, value_func, ttl: Union[int, timedelta] = 3600, *args, **kwargs) -> Any:
        """Get from cache or set if not exists"""
        # Try to get from cache first
        cached_value = self.get(prefix, *args, **kwargs)
        if cached_value is not None:
            return cached_value
        
        # If not in cache, call function to get value
        try:
            value = value_func()
            self.set(prefix, value, ttl, *args, **kwargs)
            return value
        except Exception as e:
            logger.error(f"Cache get_or_set error: {e}")
            return value_func()  # Return value even if cache fails
    
    def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a specific user"""
        patterns = [
            f"user:{user_id}:*",
            f"tasks:user:{user_id}:*",
            f"goals:user:{user_id}:*",
            f"schedule:user:{user_id}:*",
            f"flashcards:user:{user_id}:*",
            f"notifications:user:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.clear_pattern(pattern)
        
        return total_deleted

# Global cache instance
cache_service = CacheService()

# Cache decorator for functions
def cached(prefix: str, ttl: Union[int, timedelta] = 3600):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{prefix}:{func.__name__}"
            return cache_service.get_or_set(cache_key, lambda: func(*args, **kwargs), ttl, *args, **kwargs)
        return wrapper
    return decorator

# Async cache decorator
def async_cached(prefix: str, ttl: Union[int, timedelta] = 3600):
    """Decorator to cache async function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{prefix}:{func.__name__}"
            
            # Try to get from cache first
            cached_value = cache_service.get(cache_key, *args, **kwargs)
            if cached_value is not None:
                return cached_value
            
            # If not in cache, call function to get value
            try:
                value = await func(*args, **kwargs)
                cache_service.set(cache_key, value, ttl, *args, **kwargs)
                return value
            except Exception as e:
                logger.error(f"Async cache error: {e}")
                return await func(*args, **kwargs)  # Return value even if cache fails
        return wrapper
    return decorator 
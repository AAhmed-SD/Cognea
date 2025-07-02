"""
AI Cache Service with Enhanced Redis Integration
- Specialized caching for AI operations
- Intelligent cache invalidation
- Performance optimization
- User-specific cache management
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from functools import wraps

from services.redis_cache import enhanced_cache
from services.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class AICacheService:
    """Specialized cache service for AI operations"""

    def __init__(self):
        self.supabase = get_supabase_client()

        # TTL configuration for different AI operations
        self.ttl_config = {
            "ai_insights": 1800,  # 30 minutes
            "ai_planning": 900,  # 15 minutes
            "ai_flashcards": 3600,  # 1 hour
            "ai_analysis": 1200,  # 20 minutes
            "ai_suggestions": 600,  # 10 minutes
            "ai_summary": 2400,  # 40 minutes
            "ai_optimization": 1800,  # 30 minutes
            "ai_feedback": 300,  # 5 minutes
            "ai_review": 600,  # 10 minutes
        }

    def _generate_ai_cache_key(
        self, operation: str, user_id: str, data_hash: str = None, **kwargs
    ) -> str:
        """Generate cache key for AI operations"""
        key_parts = [f"ai_cache:ai:{operation}:user:{user_id}"]

        # Add data hash if provided
        if data_hash:
            key_parts.append(f"data:{data_hash}")

        # Add additional parameters
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (dict, list)):
                # Hash complex objects (non-security use)
                value_hash = hashlib.sha256(
                    json.dumps(value, sort_keys=True).encode()
                ).hexdigest()[:12]
                key_parts.append(f"{key}:{value_hash}")
            else:
                key_parts.append(f"{key}:{value}")

        return ":".join(key_parts)

    def _hash_user_data(self, user_data: Dict) -> str:
        """Create a hash of user data for cache invalidation"""
        if not user_data:
            return "empty"

        # Sort and hash the data (non-security use)
        sorted_data = json.dumps(user_data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]

    async def get_cached_ai_response(
        self, operation: str, user_id: str, user_data: Dict = None, **kwargs
    ) -> Optional[Any]:
        """Get cached AI response if available and valid"""
        try:
            # Create data hash for cache key
            data_hash = self._hash_user_data(user_data) if user_data else None

            # Generate cache key
            cache_key = self._generate_ai_cache_key(
                operation, user_id, data_hash, **kwargs
            )

            # Get from enhanced cache
            cached_response = await enhanced_cache.get("ai_cache", cache_key)

            if cached_response:
                logger.info(f"AI cache hit for {operation} - user {user_id}")
                return cached_response

            logger.debug(f"AI cache miss for {operation} - user {user_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting cached AI response: {e}")
            return None

    async def set_cached_ai_response(
        self,
        operation: str,
        user_id: str,
        response: Any,
        user_data: Dict = None,
        **kwargs,
    ) -> bool:
        """Cache AI response with appropriate TTL"""
        try:
            # Create data hash for cache key
            data_hash = self._hash_user_data(user_data) if user_data else None

            # Generate cache key
            cache_key = self._generate_ai_cache_key(
                operation, user_id, data_hash, **kwargs
            )

            # Get TTL for this operation
            ttl = self.ttl_config.get(operation, 1800)  # Default 30 minutes

            # Add metadata to response
            cached_data = {
                "response": response,
                "cached_at": datetime.utcnow().isoformat(),
                "operation": operation,
                "user_id": user_id,
                "data_hash": data_hash,
                "ttl": ttl,
            }

            # Set in enhanced cache
            success = await enhanced_cache.set("ai_cache", cached_data, ttl, cache_key)

            if success:
                logger.info(f"Cached AI response for {operation} - user {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error setting cached AI response: {e}")
            return False

    async def invalidate_user_ai_cache(
        self, user_id: str, operations: List[str] = None
    ) -> int:
        """Invalidate AI cache for specific user and operations"""
        try:
            if operations:
                patterns = [f"ai_cache:ai:{op}:user:{user_id}:*" for op in operations]
            else:
                patterns = [f"ai_cache:ai:*:user:{user_id}:*"]

            total_deleted = 0
            for pattern in patterns:
                deleted = await enhanced_cache.clear_pattern(pattern)
                total_deleted += deleted

            logger.info(
                f"Invalidated {total_deleted} AI cache entries for user {user_id}"
            )
            return total_deleted

        except Exception as e:
            logger.error(f"Error invalidating AI cache: {e}")
            return 0

    async def should_use_cache(
        self, operation: str, user_id: str, user_data: Dict = None
    ) -> bool:
        """Determine if cache should be used based on various factors"""
        try:
            # Check if user has recent data changes
            recent_changes = await self._check_recent_user_changes(user_id, operation)
            if recent_changes:
                logger.debug(
                    f"Skipping cache for {operation} - recent changes detected"
                )
                return False

            # Check if user has exceeded cache usage limits
            cache_usage = await self._get_user_cache_usage(user_id)
            if cache_usage > 100:  # Limit cache entries per user
                logger.debug(f"Skipping cache for {operation} - high cache usage")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking cache usage: {e}")
            return True  # Default to using cache

    async def _check_recent_user_changes(self, user_id: str, operation: str) -> bool:
        """Check if user has recent changes that would invalidate cache"""
        try:
            # Check for recent updates in relevant tables
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)

            # Check tasks, goals, schedule blocks, etc.
            tables_to_check = {
                "ai_insights": ["tasks", "goals", "schedule_blocks"],
                "ai_planning": ["tasks", "goals", "schedule_blocks"],
                "ai_flashcards": ["flashcards"],
                "ai_analysis": ["tasks", "goals", "habits"],
                "ai_suggestions": ["habits", "goals"],
                "ai_summary": ["tasks", "goals", "schedule_blocks"],
                "ai_optimization": ["tasks", "schedule_blocks"],
            }

            tables = tables_to_check.get(operation, ["tasks", "goals"])

            for table in tables:
                result = (
                    self.supabase.table(table)
                    .select("updated_at")
                    .eq("user_id", user_id)
                    .gte("updated_at", cutoff_time.isoformat())
                    .limit(1)
                    .execute()
                )

                if result.data:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking recent changes: {e}")
            return False

    async def _get_user_cache_usage(self, user_id: str) -> int:
        """Get number of cache entries for a user"""
        try:
            pattern = f"ai_cache:ai:*:user:{user_id}:*"
            keys = (
                await enhanced_cache.client.keys(pattern)
                if enhanced_cache.client
                else []
            )
            return len(keys)
        except Exception as e:
            logger.error(f"Error getting cache usage: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if not enhanced_cache.client:
                return {"error": "Cache not available"}

            # Get all AI cache keys
            ai_keys = enhanced_cache.client.keys("ai_cache:*")

            # Group by operation
            operation_stats = {}
            for key in ai_keys:
                parts = key.split(":")
                if len(parts) >= 3:
                    operation = parts[2]
                    operation_stats[operation] = operation_stats.get(operation, 0) + 1

            return {
                "total_ai_cache_entries": len(ai_keys),
                "operations": operation_stats,
                "cache_enabled": True,
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}


# Global AI cache instance
ai_cache_service = AICacheService()


# AI cache decorator
def ai_cached(operation: str, ttl: Optional[int] = None):
    """Decorator to cache AI function results"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id and user_data from function arguments
            user_id = None
            user_data = None

            # Look for user_id in kwargs or first argument
            if "user_id" in kwargs:
                user_id = kwargs["user_id"]
            elif args and hasattr(args[0], "user_id"):
                user_id = args[0].user_id

            # Look for user_data in kwargs
            if "user_data" in kwargs:
                user_data = kwargs["user_data"]

            if not user_id:
                logger.warning(f"No user_id found for AI cache operation: {operation}")
                return await func(*args, **kwargs)

            # Check if we should use cache
            should_cache = await ai_cache_service.should_use_cache(
                operation, user_id, user_data
            )
            if not should_cache:
                return await func(*args, **kwargs)

            # Try to get from cache
            cached_response = await ai_cache_service.get_cached_ai_response(
                operation, user_id, user_data, **kwargs
            )

            if cached_response:
                return cached_response.get("response")

            # If not in cache, execute function and cache result
            result = await func(*args, **kwargs)

            # Cache the result
            await ai_cache_service.set_cached_ai_response(
                operation, user_id, result, user_data, **kwargs
            )

            return result

        return wrapper

    return decorator


# Cache invalidation function
async def invalidate_ai_cache_for_user(user_id: str, operations: List[str] = None):
    """Invalidate AI cache for a specific user"""
    return await ai_cache_service.invalidate_user_ai_cache(user_id, operations)

"""
AI-specific caching service for heavy AI endpoints
"""

import hashlib
import json
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from services.cache import cache_service
from services.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class AICacheService:
    """Specialized caching service for AI endpoints with intelligent invalidation"""

    def __init__(self):
        self.supabase = get_supabase_client()
        
        # Cache TTL configurations for different AI operations
        self.ttl_config = {
            "ai_insights": 3600,  # 1 hour - insights change slowly
            "ai_planning": 1800,  # 30 minutes - plans can change
            "ai_flashcards": 7200,  # 2 hours - flashcards are stable
            "ai_analysis": 900,   # 15 minutes - analysis can be frequent
            "ai_suggestions": 3600,  # 1 hour - suggestions are stable
            "ai_summary": 1800,   # 30 minutes - summaries can update
            "ai_optimization": 600,  # 10 minutes - optimizations change quickly
        }

    def _generate_ai_cache_key(
        self, 
        operation: str, 
        user_id: str, 
        data_hash: str = None,
        **kwargs
    ) -> str:
        """Generate cache key for AI operations with data fingerprinting"""
        key_parts = [f"ai:{operation}", f"user:{user_id}"]
        
        # Add data hash if provided
        if data_hash:
            key_parts.append(f"data:{data_hash}")
        
        # Add additional parameters
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (dict, list)):
                # Hash complex objects
                value_hash = hashlib.md5(json.dumps(value, sort_keys=True).encode()).hexdigest()[:8]
                key_parts.append(f"{key}:{value_hash}")
            else:
                key_parts.append(f"{key}:{value}")
        
        return ":".join(key_parts)

    def _hash_user_data(self, user_data: Dict) -> str:
        """Create a hash of user data for cache invalidation"""
        if not user_data:
            return "empty"
        
        # Sort and hash the data
        sorted_data = json.dumps(user_data, sort_keys=True, default=str)
        return hashlib.md5(sorted_data.encode()).hexdigest()[:12]

    async def get_cached_ai_response(
        self, 
        operation: str, 
        user_id: str, 
        user_data: Dict = None,
        **kwargs
    ) -> Optional[Any]:
        """Get cached AI response if available and valid"""
        try:
            # Create data hash for cache key
            data_hash = self._hash_user_data(user_data) if user_data else None
            
            # Generate cache key
            cache_key = self._generate_ai_cache_key(operation, user_id, data_hash, **kwargs)
            
            # Get from cache
            cached_response = cache_service.get("ai_cache", cache_key)
            
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
        **kwargs
    ) -> bool:
        """Cache AI response with appropriate TTL"""
        try:
            # Create data hash for cache key
            data_hash = self._hash_user_data(user_data) if user_data else None
            
            # Generate cache key
            cache_key = self._generate_ai_cache_key(operation, user_id, data_hash, **kwargs)
            
            # Get TTL for this operation
            ttl = self.ttl_config.get(operation, 1800)  # Default 30 minutes
            
            # Add metadata to response
            cached_data = {
                "response": response,
                "cached_at": datetime.utcnow().isoformat(),
                "operation": operation,
                "user_id": user_id,
                "data_hash": data_hash,
                "ttl": ttl
            }
            
            # Set in cache
            success = cache_service.set("ai_cache", cached_data, ttl, cache_key)
            
            if success:
                logger.info(f"Cached AI response for {operation} - user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting cached AI response: {e}")
            return False

    async def invalidate_user_ai_cache(self, user_id: str, operations: List[str] = None) -> int:
        """Invalidate AI cache for specific user and operations"""
        try:
            if operations:
                patterns = [f"ai_cache:ai:{op}:user:{user_id}:*" for op in operations]
            else:
                patterns = [f"ai_cache:ai:*:user:{user_id}:*"]
            
            total_deleted = 0
            for pattern in patterns:
                deleted = cache_service.clear_pattern(pattern)
                total_deleted += deleted
            
            logger.info(f"Invalidated {total_deleted} AI cache entries for user {user_id}")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error invalidating AI cache: {e}")
            return 0

    async def should_use_cache(
        self, 
        operation: str, 
        user_id: str, 
        user_data: Dict = None
    ) -> bool:
        """Determine if cache should be used based on various factors"""
        try:
            # Check if user has recent data changes
            recent_changes = await self._check_recent_user_changes(user_id, operation)
            if recent_changes:
                logger.debug(f"Skipping cache for {operation} - recent changes detected")
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
                "ai_optimization": ["tasks", "schedule_blocks"]
            }
            
            tables = tables_to_check.get(operation, ["tasks", "goals"])
            
            for table in tables:
                result = self.supabase.table(table).select("updated_at").eq(
                    "user_id", user_id
                ).gte("updated_at", cutoff_time.isoformat()).limit(1).execute()
                
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
            keys = cache_service.client.keys(pattern) if cache_service.client else []
            return len(keys)
        except Exception as e:
            logger.error(f"Error getting cache usage: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if not cache_service.client:
                return {"error": "Cache not available"}
            
            # Get all AI cache keys
            ai_keys = cache_service.client.keys("ai_cache:*")
            
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
                "cache_enabled": True
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}


# Global AI cache instance
ai_cache_service = AICacheService()


# Decorator for AI endpoint caching
def ai_cached(operation: str, ttl: Optional[int] = None):
    """Decorator to cache AI endpoint responses"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id and user_data from function arguments
            user_id = None
            user_data = None
            
            # Look for user_id in kwargs or first argument
            if 'current_user' in kwargs:
                user_id = kwargs['current_user'].get('id')
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            elif args and isinstance(args[0], dict) and 'id' in args[0]:
                user_id = args[0]['id']
            
            # Look for user data in request objects
            for arg in args:
                if hasattr(arg, 'model_dump'):
                    user_data = arg.model_dump()
                    break
                elif isinstance(arg, dict):
                    user_data = arg
                    break
            
            if not user_id:
                # If no user_id found, skip caching
                return await func(*args, **kwargs)
            
            # Check if we should use cache
            should_cache = await ai_cache_service.should_use_cache(operation, user_id, user_data)
            if not should_cache:
                return await func(*args, **kwargs)
            
            # Try to get from cache
            cached_response = await ai_cache_service.get_cached_ai_response(
                operation, user_id, user_data, **kwargs
            )
            
            if cached_response:
                return cached_response["response"]
            
            # Generate response
            response = await func(*args, **kwargs)
            
            # Cache the response
            await ai_cache_service.set_cached_ai_response(
                operation, user_id, response, user_data, **kwargs
            )
            
            return response
        
        return wrapper
    return decorator


# Utility function to invalidate cache when user data changes
async def invalidate_ai_cache_for_user(user_id: str, operations: List[str] = None):
    """Invalidate AI cache when user data changes"""
    await ai_cache_service.invalidate_user_ai_cache(user_id, operations) 
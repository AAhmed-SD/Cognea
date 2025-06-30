"""
Cost tracking service for monitoring OpenAI API usage and costs.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from services.redis_client import get_redis_client
from services.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class CostTrackingService:
    def __init__(self):
        self.redis_client = get_redis_client()
        self.supabase = get_supabase_client()
        
    async def track_api_call(
        self, 
        user_id: str, 
        endpoint: str, 
        model: str, 
        input_tokens: int, 
        output_tokens: int,
        cost_usd: float
    ):
        """Track an API call and its associated cost."""
        try:
            # Store in Redis for real-time tracking
            today = datetime.utcnow().strftime("%Y-%m-%d")
            month = datetime.utcnow().strftime("%Y-%m")
            
            # Daily tracking
            daily_key = f"cost:daily:{user_id}:{today}"
            daily_cost = self.redis_client.get(daily_key) or 0
            self.redis_client.set(daily_key, float(daily_cost) + cost_usd, ex=86400)  # 24 hours
            
            # Monthly tracking
            monthly_key = f"cost:monthly:{user_id}:{month}"
            monthly_cost = self.redis_client.get(monthly_key) or 0
            self.redis_client.set(monthly_key, float(monthly_cost) + cost_usd, ex=2592000)  # 30 days
            
            # Token tracking
            token_key = f"tokens:{user_id}:{today}"
            current_tokens = self.redis_client.get(token_key) or 0
            self.redis_client.set(token_key, int(current_tokens) + input_tokens + output_tokens, ex=86400)
            
            # Store detailed record in Supabase
            usage_record = {
                "user_id": user_id,
                "endpoint": endpoint,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": cost_usd,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("api_usage").insert(usage_record).execute()
            
            if not result.data:
                logger.error(f"Failed to store API usage record for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error tracking API call: {e}")
    
    async def get_user_usage_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage summary for a user."""
        try:
            # Get from Redis first (faster)
            today = datetime.utcnow().strftime("%Y-%m-%d")
            month = datetime.utcnow().strftime("%Y-%m")
            
            daily_cost = float(self.redis_client.get(f"cost:daily:{user_id}:{today}") or 0)
            monthly_cost = float(self.redis_client.get(f"cost:monthly:{user_id}:{month}") or 0)
            daily_tokens = int(self.redis_client.get(f"tokens:{user_id}:{today}") or 0)
            
            # Get detailed data from Supabase
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.supabase.table("api_usage").select("*").eq("user_id", user_id).gte("created_at", start_date).execute()
            
            total_cost = sum(record["cost_usd"] for record in result.data)
            total_tokens = sum(record["total_tokens"] for record in result.data)
            
            return {
                "daily_cost": daily_cost,
                "monthly_cost": monthly_cost,
                "total_cost": total_cost,
                "daily_tokens": daily_tokens,
                "total_tokens": total_tokens,
                "usage_count": len(result.data),
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {
                "daily_cost": 0,
                "monthly_cost": 0,
                "total_cost": 0,
                "daily_tokens": 0,
                "total_tokens": 0,
                "usage_count": 0,
                "period_days": days
            }
    
    async def check_budget_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if user has exceeded budget limits."""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            month = datetime.utcnow().strftime("%Y-%m")
            
            daily_cost = float(self.redis_client.get(f"cost:daily:{user_id}:{today}") or 0)
            monthly_cost = float(self.redis_client.get(f"cost:monthly:{user_id}:{month}") or 0)
            
            # Get user's budget limits from settings
            result = self.supabase.table("user_settings").select("daily_budget_limit_usd, monthly_budget_limit_usd").eq("user_id", user_id).execute()
            
            if result.data:
                settings = result.data[0]
                daily_limit = settings.get("daily_budget_limit_usd", 10.0)
                monthly_limit = settings.get("monthly_budget_limit_usd", 100.0)
            else:
                daily_limit = 10.0
                monthly_limit = 100.0
            
            return {
                "daily_cost": daily_cost,
                "monthly_cost": monthly_cost,
                "daily_limit": daily_limit,
                "monthly_limit": monthly_limit,
                "daily_exceeded": daily_cost >= daily_limit,
                "monthly_exceeded": monthly_cost >= monthly_limit
            }
            
        except Exception as e:
            logger.error(f"Error checking budget limits: {e}")
            return {
                "daily_cost": 0,
                "monthly_cost": 0,
                "daily_limit": 10.0,
                "monthly_limit": 100.0,
                "daily_exceeded": False,
                "monthly_exceeded": False
            }

# Global instance
cost_tracking_service = CostTrackingService() 
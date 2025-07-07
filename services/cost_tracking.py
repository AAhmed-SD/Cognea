"""
Cost tracking service for OpenAI API usage
"""

import logging
from datetime import datetime

from services.supabase import supabase_client

logger = logging.getLogger(__name__)


class CostTracker:
    """Track OpenAI API usage and costs"""

    def __init__(self):
    pass
        # OpenAI pricing per 1K tokens (as of 2024)
        self.pricing = {
            "gpt-4-turbo-preview": {
                "input": 0.01,
                "output": 0.03,
            },  # $0.01/$0.03 per 1K tokens
            "gpt-4": {"input": 0.03, "output": 0.06},  # $0.03/$0.06 per 1K tokens
            "gpt-3.5-turbo": {
                "input": 0.001,
                "output": 0.002,
            },  # $0.001/$0.002 per 1K tokens
        }

    def track_openai_usage(
        self,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
    ):
    pass
        """Track OpenAI API usage and calculate costs"""

        try:
            # Calculate costs
            input_cost = (input_tokens / 1000) * self.pricing.get(model, {}).get(
                "input", 0
            )
            output_cost = (output_tokens / 1000) * self.pricing.get(model, {}).get(
                "output", 0
            )
            total_cost = input_cost + output_cost

            # Store usage record
            usage_record = {
                "user_id": user_id,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
                "total_cost_usd": round(total_cost, 6),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Insert into database
            supabase_client.table("openai_usage").insert(usage_record).execute()

            # Update daily/monthly totals
            self._update_usage_totals(user_id, total_cost)

            logger.info(
                f"Tracked OpenAI usage for user {user_id}: {total_tokens} tokens, ${total_cost:.6f}"
            )

        except Exception as e:
            logger.error(f"Error tracking OpenAI usage: {str(e)}")

    async def track_api_call(
        self,
        user_id: str,
        endpoint: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ):
    pass
        """Track API call with detailed information"""
        try:
            total_tokens = input_tokens + output_tokens

            # Store usage record
            usage_record = {
                "user_id": user_id,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "input_cost_usd": (
                    round(cost_usd * (input_tokens / total_tokens), 6)
                    if total_tokens > 0
                    else 0
                ),
                "output_cost_usd": (
                    round(cost_usd * (output_tokens / total_tokens), 6)
                    if total_tokens > 0
                    else cost_usd
                ),
                "total_cost_usd": round(cost_usd, 6),
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Insert into database
            supabase_client.table("openai_usage").insert(usage_record).execute()

            # Update daily/monthly totals
            self._update_usage_totals(user_id, cost_usd)

            logger.info(
                f"Tracked API call for user {user_id}: {endpoint}, {total_tokens} tokens, ${cost_usd:.6f}"
            )

        except Exception as e:
            logger.error(f"Error tracking API call: {str(e)}")

    async def check_budget_limits(self, user_id: str) -> dict:
        """Check if user has exceeded budget limits"""
        try:
            usage_summary = self.get_user_usage_summary(user_id)

            daily_exceeded = (
                usage_summary["daily"]["total_cost_usd"]
                > usage_summary["limits"]["daily_limit_usd"]
            )
            monthly_exceeded = (
                usage_summary["monthly"]["total_cost_usd"]
                > usage_summary["limits"]["monthly_limit_usd"]
            )

            return {
                "can_use": not (daily_exceeded or monthly_exceeded),
                "daily_exceeded": daily_exceeded,
                "monthly_exceeded": monthly_exceeded,
                "usage": usage_summary,
            }

        except Exception as e:
            logger.error(f"Error checking budget limits: {str(e)}")
            return {
                "can_use": True,  # Default to allowing usage if check fails
                "daily_exceeded": False,
                "monthly_exceeded": False,
                "usage": {
                    "daily": {"total_cost_usd": 0, "total_requests": 0},
                    "monthly": {"total_cost_usd": 0, "total_requests": 0},
                    "limits": {"daily_limit_usd": 10.0, "monthly_limit_usd": 100.0},
                },
            }

    def _update_usage_totals(self, user_id: str, cost: float):
    pass
        """Update daily and monthly usage totals"""

        try:
            now = datetime.utcnow()
            today = now.date()
            month_start = now.replace(day=1).date()

            # Update daily total
            daily_key = f"usage_daily:{user_id}:{today.isoformat()}"
            self._increment_usage_total(daily_key, cost)

            # Update monthly total
            monthly_key = f"usage_monthly:{user_id}:{month_start.isoformat()}"
            self._increment_usage_total(monthly_key, cost)

        except Exception as e:
            logger.error(f"Error updating usage totals: {str(e)}")

    def _increment_usage_total(self, key: str, cost: float):
    pass
        """Increment usage total in database"""

        try:
            # Get current total
            response = (
                supabase_client.table("usage_totals")
                .select("total_cost_usd, total_requests")
                .eq("key", key)
                .execute()
            )

            if response.data:
                # Update existing record
                current = response.data[0]
                new_total = current["total_cost_usd"] + cost
                new_requests = current["total_requests"] + 1

                supabase_client.table("usage_totals").update(
                    {
                        "total_cost_usd": new_total,
                        "total_requests": new_requests,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).eq("key", key).execute()
            else:
                # Create new record
                supabase_client.table("usage_totals").insert(
                    {
                        "key": key,
                        "total_cost_usd": cost,
                        "total_requests": 1,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).execute()

        except Exception as e:
            logger.error(f"Error incrementing usage total: {str(e)}")

    def get_user_usage_summary(self, user_id: str) -> dict:
        """Get usage summary for a user"""

        try:
            now = datetime.utcnow()
            today = now.date()
            month_start = now.replace(day=1).date()

            # Get daily usage
            daily_response = (
                supabase_client.table("usage_totals")
                .select("total_cost_usd, total_requests")
                .eq("key", f"usage_daily:{user_id}:{today.isoformat()}")
                .execute()
            )

            daily_usage = (
                daily_response.data[0]
                if daily_response.data
                else {"total_cost_usd": 0, "total_requests": 0}
            )

            # Get monthly usage
            monthly_response = (
                supabase_client.table("usage_totals")
                .select("total_cost_usd, total_requests")
                .eq("key", f"usage_monthly:{user_id}:{month_start.isoformat()}")
                .execute()
            )

            monthly_usage = (
                monthly_response.data[0]
                if monthly_response.data
                else {"total_cost_usd": 0, "total_requests": 0}
            )

            return {
                "daily": daily_usage,
                "monthly": monthly_usage,
                "limits": {
                    "daily_limit_usd": 10.0,  # From config
                    "monthly_limit_usd": 100.0,  # From config
                },
            }

        except Exception as e:
            logger.error(f"Error getting user usage summary: {str(e)}")
            return {
                "daily": {"total_cost_usd": 0, "total_requests": 0},
                "monthly": {"total_cost_usd": 0, "total_requests": 0},
                "limits": {"daily_limit_usd": 10.0, "monthly_limit_usd": 100.0},
            }

    def check_usage_limits(self, user_id: str) -> dict:
        """Check if user has exceeded usage limits"""

        try:
            usage_summary = self.get_user_usage_summary(user_id)

            daily_exceeded = (
                usage_summary["daily"]["total_cost_usd"]
                > usage_summary["limits"]["daily_limit_usd"]
            )
            monthly_exceeded = (
                usage_summary["monthly"]["total_cost_usd"]
                > usage_summary["limits"]["monthly_limit_usd"]
            )

            return {
                "can_use": not (daily_exceeded or monthly_exceeded),
                "daily_exceeded": daily_exceeded,
                "monthly_exceeded": monthly_exceeded,
                "usage": usage_summary,
            }

        except Exception as e:
            logger.error(f"Error checking usage limits: {str(e)}")
            return {
                "can_use": True,  # Default to allowing usage if check fails
                "daily_exceeded": False,
                "monthly_exceeded": False,
                "usage": {
                    "daily": {"total_cost_usd": 0, "total_requests": 0},
                    "monthly": {"total_cost_usd": 0, "total_requests": 0},
                    "limits": {"daily_limit_usd": 10.0, "monthly_limit_usd": 100.0},
                },
            }


# Global instance
cost_tracking_service = CostTracker()

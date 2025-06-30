"""
AI Context Manager for building user context and managing conversation memory
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

from services.supabase import supabase_client
from services.cache import cache_service

logger = logging.getLogger(__name__)

class UserContext:
    """User context data structure"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tasks = []
        self.goals = []
        self.habits = []
        self.schedule_blocks = []
        self.flashcards = []
        self.productivity_data = {}
        self.preferences = {}
        self.conversation_history = []
        self.last_updated = None
    
    def to_dict(self) -> Dict:
        """Convert context to dictionary"""
        return {
            "user_id": self.user_id,
            "tasks": self.tasks,
            "goals": self.goals,
            "habits": self.habits,
            "schedule_blocks": self.schedule_blocks,
            "flashcards": self.flashcards,
            "productivity_data": self.productivity_data,
            "preferences": self.preferences,
            "conversation_history": self.conversation_history[-10:],  # Keep last 10 conversations
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

class ContextManager:
    """Manages user context for AI interactions"""
    
    def __init__(self):
        self.context_cache_ttl = 1800  # 30 minutes
        self.conversation_memory_size = 50  # Keep last 50 messages
    
    async def build_user_context(self, user_id: str, force_refresh: bool = False) -> UserContext:
        """Build comprehensive user context from all data sources"""
        
        # Check cache first
        cache_key = f"user_context:{user_id}"
        if not force_refresh:
            cached_context = await cache_service.get(cache_key)
            if cached_context:
                logger.info(f"Returning cached context for user {user_id}")
                context = UserContext(user_id)
                context.__dict__.update(cached_context)
                return context
        
        logger.info(f"Building fresh context for user {user_id}")
        context = UserContext(user_id)
        
        try:
            # Fetch all user data concurrently
            tasks = [
                self._fetch_tasks(user_id),
                self._fetch_goals(user_id),
                self._fetch_habits(user_id),
                self._fetch_schedule_blocks(user_id),
                self._fetch_flashcards(user_id),
                self._fetch_productivity_data(user_id),
                self._fetch_user_preferences(user_id),
                self._fetch_conversation_history(user_id)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            context.tasks = results[0] if not isinstance(results[0], Exception) else []
            context.goals = results[1] if not isinstance(results[1], Exception) else []
            context.habits = results[2] if not isinstance(results[2], Exception) else []
            context.schedule_blocks = results[3] if not isinstance(results[3], Exception) else []
            context.flashcards = results[4] if not isinstance(results[4], Exception) else []
            context.productivity_data = results[5] if not isinstance(results[5], Exception) else {}
            context.preferences = results[6] if not isinstance(results[6], Exception) else {}
            context.conversation_history = results[7] if not isinstance(results[7], Exception) else []
            
            context.last_updated = datetime.utcnow()
            
            # Cache the context
            await cache_service.set(cache_key, context.to_dict(), expire=self.context_cache_ttl)
            
            logger.info(f"Context built successfully for user {user_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error building context for user {user_id}: {str(e)}")
            raise
    
    async def _fetch_tasks(self, user_id: str) -> List[Dict]:
        """Fetch user tasks"""
        try:
            response = await supabase_client.table("tasks").select("*").eq("user_id", user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching tasks for user {user_id}: {str(e)}")
            return []
    
    async def _fetch_goals(self, user_id: str) -> List[Dict]:
        """Fetch user goals"""
        try:
            response = await supabase_client.table("goals").select("*").eq("user_id", user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching goals for user {user_id}: {str(e)}")
            return []
    
    async def _fetch_habits(self, user_id: str) -> List[Dict]:
        """Fetch user habits"""
        try:
            response = await supabase_client.table("habits").select("*").eq("user_id", user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching habits for user {user_id}: {str(e)}")
            return []
    
    async def _fetch_schedule_blocks(self, user_id: str) -> List[Dict]:
        """Fetch user schedule blocks"""
        try:
            response = await supabase_client.table("schedule_blocks").select("*").eq("user_id", user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching schedule blocks for user {user_id}: {str(e)}")
            return []
    
    async def _fetch_flashcards(self, user_id: str) -> List[Dict]:
        """Fetch user flashcards"""
        try:
            response = await supabase_client.table("flashcards").select("*").eq("user_id", user_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching flashcards for user {user_id}: {str(e)}")
            return []
    
    async def _fetch_productivity_data(self, user_id: str) -> Dict:
        """Fetch and calculate productivity data"""
        try:
            # Get recent tasks and their completion data
            tasks_response = await supabase_client.table("tasks").select(
                "id, title, status, priority, created_at, completed_at, estimated_time"
            ).eq("user_id", user_id).gte("created_at", (datetime.utcnow() - timedelta(days=30)).isoformat()).execute()
            
            tasks = tasks_response.data or []
            
            # Calculate productivity metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Calculate average completion time
            completed_with_time = [t for t in tasks if t.get("completed_at") and t.get("created_at")]
            avg_completion_time = 0
            if completed_with_time:
                total_time = sum([
                    (datetime.fromisoformat(t["completed_at"]) - datetime.fromisoformat(t["created_at"])).total_seconds()
                    for t in completed_with_time
                ])
                avg_completion_time = total_time / len(completed_with_time)
            
            # Priority distribution
            priority_counts = defaultdict(int)
            for task in tasks:
                priority_counts[task.get("priority", "medium")] += 1
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": completion_rate,
                "avg_completion_time_hours": avg_completion_time / 3600,
                "priority_distribution": dict(priority_counts),
                "last_30_days": True
            }
            
        except Exception as e:
            logger.error(f"Error fetching productivity data for user {user_id}: {str(e)}")
            return {}
    
    async def _fetch_user_preferences(self, user_id: str) -> Dict:
        """Fetch user preferences and settings"""
        try:
            response = await supabase_client.table("user_settings").select("*").eq("user_id", user_id).execute()
            settings = response.data[0] if response.data else {}
            
            # Extract relevant preferences
            preferences = {
                "work_hours": settings.get("work_hours", {"start": "09:00", "end": "17:00"}),
                "timezone": settings.get("timezone", "UTC"),
                "notification_preferences": settings.get("notification_preferences", {}),
                "productivity_goals": settings.get("productivity_goals", {}),
                "focus_preferences": settings.get("focus_preferences", {}),
                "break_preferences": settings.get("break_preferences", {})
            }
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error fetching user preferences for user {user_id}: {str(e)}")
            return {}
    
    async def _fetch_conversation_history(self, user_id: str) -> List[Dict]:
        """Fetch recent conversation history"""
        try:
            response = await supabase_client.table("ai_conversations").select(
                "conversation_data, created_at"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
            
            conversations = []
            for conv in response.data or []:
                conv_data = conv.get("conversation_data", {})
                if isinstance(conv_data, str):
                    try:
                        conv_data = json.loads(conv_data)
                    except:
                        conv_data = {}
                
                conversations.extend(conv_data.get("messages", []))
            
            return conversations[-self.conversation_memory_size:]
            
        except Exception as e:
            logger.error(f"Error fetching conversation history for user {user_id}: {str(e)}")
            return []
    
    async def add_conversation_message(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add a new message to conversation history"""
        
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Get current conversation or create new one
            response = await supabase_client.table("ai_conversations").select(
                "id, conversation_data"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
            
            if response.data:
                # Update existing conversation
                conv_id = response.data[0]["id"]
                conv_data = response.data[0].get("conversation_data", {})
                if isinstance(conv_data, str):
                    try:
                        conv_data = json.loads(conv_data)
                    except:
                        conv_data = {"messages": []}
                
                conv_data["messages"] = conv_data.get("messages", [])
                conv_data["messages"].append(message)
                
                # Keep only recent messages
                conv_data["messages"] = conv_data["messages"][-self.conversation_memory_size:]
                
                await supabase_client.table("ai_conversations").update({
                    "conversation_data": conv_data,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", conv_id).execute()
                
            else:
                # Create new conversation
                conv_data = {
                    "messages": [message],
                    "created_at": datetime.utcnow().isoformat()
                }
                
                await supabase_client.table("ai_conversations").insert({
                    "user_id": user_id,
                    "conversation_data": conv_data,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            
            # Invalidate context cache
            await cache_service.delete(f"user_context:{user_id}")
            
            logger.info(f"Added conversation message for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error adding conversation message for user {user_id}: {str(e)}")
    
    async def get_context_summary(self, user_id: str) -> Dict:
        """Get a summary of user context for AI prompts"""
        
        context = await self.build_user_context(user_id)
        
        summary = {
            "user_id": user_id,
            "task_summary": {
                "total_tasks": len(context.tasks),
                "pending_tasks": len([t for t in context.tasks if t.get("status") != "completed"]),
                "completed_tasks": len([t for t in context.tasks if t.get("status") == "completed"]),
                "high_priority_tasks": len([t for t in context.tasks if t.get("priority") == "high" or t.get("priority") == "urgent"])
            },
            "goal_summary": {
                "total_goals": len(context.goals),
                "active_goals": len([g for g in context.goals if g.get("status") == "active"]),
                "completed_goals": len([g for g in context.goals if g.get("status") == "completed"])
            },
            "productivity_metrics": context.productivity_data,
            "preferences": context.preferences,
            "recent_activity": {
                "last_conversation": context.conversation_history[-1] if context.conversation_history else None,
                "recent_tasks": context.tasks[-5:] if context.tasks else [],
                "upcoming_schedule": [b for b in context.schedule_blocks if b.get("start_time") > datetime.utcnow().isoformat()][:5]
            }
        }
        
        return summary
    
    async def update_user_preferences(self, user_id: str, preferences: Dict):
        """Update user preferences and invalidate cache"""
        
        try:
            await supabase_client.table("user_settings").upsert({
                "user_id": user_id,
                **preferences,
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Invalidate context cache
            await cache_service.delete(f"user_context:{user_id}")
            
            logger.info(f"Updated preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
            raise

# Global instance
context_manager = ContextManager() 
"""
Enhanced OpenAI Service with GPT-4 Turbo, Function Calling, and Advanced Features
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
import time

from services.cost_tracking import cost_tracking_service
from services.cache import cache_service
from config.security import security_config

logger = logging.getLogger(__name__)

class FunctionCall(BaseModel):
    """Function call definition for OpenAI"""
    name: str
    description: str
    parameters: Dict[str, Any]

class AIResponse(BaseModel):
    """Structured AI response"""
    content: str
    function_calls: Optional[List[Dict]] = None
    usage: Optional[Dict] = None
    model: str
    response_time: float

class EnhancedOpenAIService:
    """Enhanced OpenAI service with advanced features"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=security_config.openai_api_key)
        self.cost_tracker = cost_tracking_service
        self.model = "gpt-4-turbo-preview"
        self.max_tokens = 4000
        self.temperature = 0.7
        
        # Function definitions for structured responses
        self.functions = {
            "create_task": FunctionCall(
                name="create_task",
                description="Create a new task with structured data",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "description": {"type": "string", "description": "Task description"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                        "due_date": {"type": "string", "description": "Due date in ISO format"},
                        "category": {"type": "string", "description": "Task category"},
                        "estimated_time": {"type": "integer", "description": "Estimated time in minutes"},
                        "subtasks": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["title"]
                }
            ),
            "schedule_block": FunctionCall(
                name="schedule_block",
                description="Create a time block for scheduling",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Block title"},
                        "start_time": {"type": "string", "description": "Start time in ISO format"},
                        "end_time": {"type": "string", "description": "End time in ISO format"},
                        "task_ids": {"type": "array", "items": {"type": "string"}},
                        "energy_level": {"type": "string", "enum": ["low", "medium", "high"]},
                        "focus_type": {"type": "string", "enum": ["deep_work", "meeting", "break", "learning"]}
                    },
                    "required": ["title", "start_time", "end_time"]
                }
            ),
            "generate_insight": FunctionCall(
                name="generate_insight",
                description="Generate productivity insights",
                parameters={
                    "type": "object",
                    "properties": {
                        "insight_type": {"type": "string", "enum": ["productivity", "scheduling", "goal", "learning"]},
                        "title": {"type": "string", "description": "Insight title"},
                        "description": {"type": "string", "description": "Insight description"},
                        "action_items": {"type": "array", "items": {"type": "string"}},
                        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
                    },
                    "required": ["insight_type", "title", "description"]
                }
            )
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        use_functions: bool = False,
        stream: bool = False,
        context: Optional[Dict] = None
    ) -> AIResponse:
        """Enhanced chat completion with function calling and streaming"""
        
        start_time = time.time()
        
        # Add context to messages if provided
        if context:
            context_message = {
                "role": "system",
                "content": f"User Context: {json.dumps(context, indent=2)}"
            }
            messages.insert(0, context_message)
        
        # Prepare function definitions if requested
        function_definitions = None
        if use_functions:
            function_definitions = [
                {
                    "name": func.name,
                    "description": func.description,
                    "parameters": func.parameters
                }
                for func in self.functions.values()
            ]
        
        try:
            # Check cache first
            cache_key = f"ai_response:{user_id}:{hash(str(messages))}"
            cached_response = await cache_service.get(cache_key)
            if cached_response and not stream:
                logger.info(f"Returning cached AI response for user {user_id}")
                return AIResponse(**cached_response)
            
            # Make API call
            if stream:
                return await self._stream_completion(messages, function_definitions, user_id)
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=function_definitions,
                    function_call="auto" if use_functions else None,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=False
                )
                
                # Process response
                content = response.choices[0].message.content or ""
                function_calls = None
                
                if response.choices[0].message.function_call:
                    function_calls = [{
                        "name": response.choices[0].message.function_call.name,
                        "arguments": json.loads(response.choices[0].message.function_call.arguments)
                    }]
                
                # Track costs
                self.cost_tracker.track_openai_usage(
                    user_id=user_id,
                    model=self.model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens
                )
                
                response_time = time.time() - start_time
                
                ai_response = AIResponse(
                    content=content,
                    function_calls=function_calls,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    model=self.model,
                    response_time=response_time
                )
                
                # Cache response
                await cache_service.set(cache_key, ai_response.dict(), expire=3600)
                
                logger.info(f"AI response generated for user {user_id} in {response_time:.2f}s")
                return ai_response
                
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise
    
    async def _stream_completion(
        self,
        messages: List[Dict[str, str]],
        function_definitions: Optional[List],
        user_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream completion for real-time responses"""
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=function_definitions,
                function_call="auto" if function_definitions else None,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            full_content = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content
            
            # Track usage after streaming completes
            # Note: OpenAI doesn't provide usage stats for streaming
            # We'll estimate based on content length
            estimated_tokens = len(full_content.split()) * 1.3
            self.cost_tracker.track_openai_usage(
                user_id=user_id,
                model=self.model,
                input_tokens=0,  # We don't have this for streaming
                output_tokens=int(estimated_tokens),
                total_tokens=int(estimated_tokens)
            )
            
        except Exception as e:
            logger.error(f"Error in stream completion: {str(e)}")
            raise
    
    async def generate_task_from_text(
        self,
        text: str,
        user_id: str,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """Generate structured task from natural language text"""
        
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant that helps users create structured tasks from natural language. 
                Analyze the text and create a well-structured task with appropriate priority, due date, and categorization."""
            },
            {
                "role": "user",
                "content": f"Create a task from this text: {text}"
            }
        ]
        
        response = await self.chat_completion(
            messages=messages,
            user_id=user_id,
            use_functions=True,
            context=user_context
        )
        
        if response.function_calls:
            return response.function_calls[0]["arguments"]
        else:
            # Fallback: parse the response manually
            return self._parse_task_from_text(response.content)
    
    async def optimize_schedule(
        self,
        tasks: List[Dict],
        schedule_blocks: List[Dict],
        user_preferences: Dict,
        user_id: str
    ) -> Dict:
        """Optimize schedule using AI"""
        
        context = {
            "tasks": tasks,
            "current_schedule": schedule_blocks,
            "user_preferences": user_preferences
        }
        
        messages = [
            {
                "role": "system",
                "content": """You are an AI scheduling assistant. Optimize the user's schedule by:
                1. Assigning tasks to optimal time blocks based on energy levels
                2. Minimizing context switching
                3. Ensuring adequate breaks
                4. Respecting user preferences and constraints"""
            },
            {
                "role": "user",
                "content": "Please optimize my schedule based on my tasks and preferences."
            }
        ]
        
        response = await self.chat_completion(
            messages=messages,
            user_id=user_id,
            use_functions=True,
            context=context
        )
        
        return {
            "optimized_schedule": response.function_calls[0]["arguments"] if response.function_calls else {},
            "insights": response.content
        }
    
    async def generate_productivity_insights(
        self,
        user_data: Dict,
        user_id: str
    ) -> List[Dict]:
        """Generate productivity insights from user data"""
        
        messages = [
            {
                "role": "system",
                "content": """You are an AI productivity analyst. Analyze the user's data and generate insights about:
                1. Productivity patterns and peak performance times
                2. Task completion trends and bottlenecks
                3. Goal progress and recommendations
                4. Potential improvements and optimizations"""
            },
            {
                "role": "user",
                "content": "Please analyze my productivity data and provide insights."
            }
        ]
        
        response = await self.chat_completion(
            messages=messages,
            user_id=user_id,
            use_functions=True,
            context=user_data
        )
        
        insights = []
        if response.function_calls:
            for call in response.function_calls:
                insights.append(call["arguments"])
        
        return insights
    
    def _parse_task_from_text(self, text: str) -> Dict:
        """Fallback parser for task creation when function calling fails"""
        # Simple parsing logic as fallback
        lines = text.split('\n')
        task_data = {
            "title": lines[0].strip() if lines else "New Task",
            "description": text,
            "priority": "medium",
            "category": "general"
        }
        
        # Try to extract priority from text
        text_lower = text.lower()
        if any(word in text_lower for word in ["urgent", "asap", "critical"]):
            task_data["priority"] = "urgent"
        elif any(word in text_lower for word in ["important", "high"]):
            task_data["priority"] = "high"
        elif any(word in text_lower for word in ["low", "when possible"]):
            task_data["priority"] = "low"
        
        return task_data

# Global instance
openai_service = EnhancedOpenAIService() 
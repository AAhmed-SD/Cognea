# Smart Scheduling Implementation Guide

## Overview

The Smart Scheduling system is a specialized AI-powered study planner that analyzes student performance, tracks memory patterns, and generates personalized study schedules. It uses the hybrid AI system to provide cost-effective, high-quality planning capabilities.

## Architecture

### Core Components

1. **SmartScheduler** (`services/ai/smart_scheduler.py`)
   - Main orchestrator for all scheduling operations
   - Integrates with the hybrid AI system
   - Handles prompt engineering and response parsing

2. **HybridAIService** (`services/ai/hybrid_ai_service.py`)
   - Routes requests to optimal AI providers
   - Manages quality thresholds and fallbacks
   - Tracks costs and performance

3. **AI Providers**
   - **Claude 3.5 Sonnet** (Primary) - Best reasoning for complex planning
   - **DeepSeek** (Secondary) - Good reasoning, cost-effective
   - **OpenAI GPT-4** (Fallback) - Reliable but expensive

## Key Features

### 1. Personalized Study Schedule Generation
- Analyzes exam dates and topic weights
- Considers flashcard performance history
- Adapts to available study time
- Respects user preferences and learning style

### 2. Memory Pattern Analysis
- Tracks flashcard performance over time
- Identifies difficult topics and learning patterns
- Recommends optimal study intervals
- Suggests learning style optimizations

### 3. Intelligent Revision Planning
- Creates focused revision plans for specific exams
- Prioritizes weak topics based on current progress
- Schedules mock exams and practice tests
- Tracks confidence metrics

## API Usage

### Generate Study Schedule

```python
from services.ai.smart_scheduler import get_smart_scheduler

scheduler = get_smart_scheduler()

result = await scheduler.generate_study_schedule(
    user_id="user_123",
    exam_dates=[
        {
            "date": "2024-02-15",
            "subject": "Organic Chemistry",
            "topics": ["Alkanes", "Alkenes", "Reactions"],
            "weight": 0.4
        }
    ],
    flashcard_performance={
        "Organic Chemistry": {
            "total_cards": 150,
            "correct_answers": 89,
            "accuracy": 0.59,
            "difficulty_level": "high"
        }
    },
    available_time={
        "monday": 3,
        "tuesday": 2,
        "wednesday": 4,
        "thursday": 2,
        "friday": 3,
        "saturday": 5,
        "sunday": 4
    },
    study_preferences={
        "preferred_session_length": 45,
        "break_duration": 15,
        "preferred_time": "evening",
        "learning_style": "visual"
    }
)
```

### Analyze Memory Patterns

```python
result = await scheduler.analyze_memory_patterns(
    user_id="user_123",
    flashcard_history=[
        {
            "flashcard_id": "fc_001",
            "topic": "Organic Chemistry",
            "correct": True,
            "timestamp": "2024-01-20T10:30:00",
            "review_count": 3
        }
    ],
    study_sessions=[
        {
            "session_id": "ss_001",
            "date": "2024-01-20",
            "duration_minutes": 90,
            "topics": ["Organic Chemistry"],
            "flashcards_reviewed": 25,
            "accuracy": 0.68
        }
    ]
)
```

### Generate Revision Plan

```python
from datetime import datetime

result = await scheduler.generate_revision_plan(
    user_id="user_123",
    exam_date=datetime(2024, 2, 15),
    topics=["Alkanes", "Alkenes", "Alkynes", "Reactions"],
    current_progress={
        "Alkanes": 0.75,
        "Alkenes": 0.45,
        "Alkynes": 0.30,
        "Reactions": 0.60
    },
    available_days=25
)
```

## Response Formats

### Study Schedule Response

```json
{
    "success": true,
    "schedule": {
        "daily_schedule": [
            {
                "date": "2024-01-25",
                "topics": ["Organic Chemistry"],
                "flashcards_to_review": ["fc_001", "fc_002"],
                "new_flashcards": ["fc_003"],
                "study_time_minutes": 120,
                "goals": ["Master alkane reactions", "Review 20 flashcards"],
                "priority": "high"
            }
        ],
        "weekly_overview": {
            "total_study_time": 840,
            "topics_covered": ["Organic Chemistry", "Calculus"],
            "weak_areas_focus": ["Alkene reactions"],
            "exam_preparation_progress": 0.65
        },
        "recommendations": [
            "Focus more on organic chemistry - 30% below target",
            "Review calculus daily - strong performance, maintain momentum"
        ]
    },
    "model_used": "claude-3-haiku",
    "provider": "claude_api",
    "cost_usd": 0.0025,
    "quality_score": 0.92
}
```

### Memory Analysis Response

```json
{
    "success": true,
    "analysis": {
        "difficult_topics": ["Organic Chemistry", "Alkene reactions"],
        "optimal_session_length": 45,
        "optimal_frequency": "daily",
        "retention_patterns": {
            "short_term": 0.85,
            "long_term": 0.72
        },
        "best_study_times": ["morning", "evening"],
        "spaced_repetition_intervals": [1, 3, 7, 14, 30],
        "learning_style": "visual",
        "recommendations": [
            "Study organic chemistry in shorter, more frequent sessions",
            "Use visual aids for alkene reactions"
        ]
    },
    "model_used": "claude-3-haiku",
    "provider": "claude_api",
    "cost_usd": 0.0018,
    "quality_score": 0.88
}
```

## Cost Optimization

### Provider Routing Strategy

| Task Type | Primary | Secondary | Fallback | Quality Threshold |
|-----------|---------|-----------|----------|-------------------|
| SMART_SCHEDULING | Claude | DeepSeek | OpenAI | 0.92 |
| MEMORY_ANALYSIS | Claude | DeepSeek | OpenAI | 0.88 |
| REVISION_PLANNING | Claude | DeepSeek | OpenAI | 0.90 |

### Expected Costs (per request)

| Provider | Input Cost | Output Cost | Total (avg) |
|----------|------------|-------------|-------------|
| Claude 3.5 Haiku | $0.25/1M | $1.25/1M | ~$0.002 |
| DeepSeek | $0.14/1M | $0.28/1M | ~$0.001 |
| OpenAI GPT-4 | $10/1M | $30/1M | ~$0.05 |

**Cost Savings:** 95-98% compared to OpenAI-only approach

## Quality Assurance

### Quality Metrics

1. **Response Completeness** - Ensures all required fields are present
2. **JSON Validity** - Validates structured output format
3. **Content Relevance** - Checks for topic-specific terminology
4. **Logical Consistency** - Verifies schedule feasibility

### Fallback Logic

1. **Primary Provider** (Claude) - Best reasoning, moderate cost
2. **Secondary Provider** (DeepSeek) - Good reasoning, low cost
3. **Fallback Provider** (OpenAI) - Reliable, high cost

If quality threshold not met, automatically tries next provider.

## Integration Points

### Database Schema

```sql
-- Study schedules
CREATE TABLE study_schedules (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    schedule_data JSONB,
    generated_at TIMESTAMP,
    model_used VARCHAR(50),
    provider VARCHAR(50),
    cost_usd DECIMAL(10,6),
    quality_score DECIMAL(3,2)
);

-- Memory analysis
CREATE TABLE memory_analyses (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    analysis_data JSONB,
    created_at TIMESTAMP,
    model_used VARCHAR(50),
    provider VARCHAR(50)
);

-- Revision plans
CREATE TABLE revision_plans (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    exam_id UUID REFERENCES exams(id),
    plan_data JSONB,
    created_at TIMESTAMP,
    model_used VARCHAR(50),
    provider VARCHAR(50)
);
```

### API Endpoints

```python
# FastAPI routes
@app.post("/api/smart-schedule/generate")
async def generate_schedule(request: ScheduleRequest):
    return await scheduler.generate_study_schedule(**request.dict())

@app.post("/api/smart-schedule/analyze-memory")
async def analyze_memory(request: MemoryAnalysisRequest):
    return await scheduler.analyze_memory_patterns(**request.dict())

@app.post("/api/smart-schedule/revision-plan")
async def generate_revision_plan(request: RevisionPlanRequest):
    return await scheduler.generate_revision_plan(**request.dict())
```

## Testing

### Run Tests

```bash
# Test hybrid AI system
python test_hybrid_ai.py

# Test smart scheduling
python test_smart_scheduling.py

# Test with real APIs (requires API keys)
python test_hybrid_ai.py --test-apis
```

### Test Coverage

- ✅ Service initialization
- ✅ Model configuration
- ✅ Cost analysis
- ✅ Provider routing
- ✅ Quality thresholds
- ✅ Fallback logic
- ✅ Response parsing
- ✅ Error handling

## Deployment Checklist

### Environment Variables

```bash
# Required API Keys
ANTHROPIC_API_KEY=your_claude_key
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key

# Optional (for self-hosted models)
LLAMA_API_URL=http://localhost:8000
```

### Dependencies

```bash
pip install aiohttp pydantic
```

### Monitoring

1. **Cost Tracking** - Monitor API usage and costs
2. **Quality Metrics** - Track quality scores and fallback rates
3. **Performance** - Monitor response times and availability
4. **User Feedback** - Collect quality ratings from students

## Future Enhancements

1. **Learning Style Adaptation** - Customize prompts based on learning preferences
2. **Real-time Adjustments** - Update schedules based on daily performance
3. **Group Study Planning** - Coordinate schedules for study groups
4. **Integration with LMS** - Connect with Canvas, Blackboard, etc.
5. **Mobile Optimization** - Optimize for mobile study sessions

## Support

For issues or questions:
1. Check the test logs for error details
2. Verify API keys are correctly set
3. Monitor the hybrid AI service health
4. Review quality thresholds and adjust if needed 
# Cognie API Documentation

## Overview
Cognie is an AI-powered productivity and scheduling web application with a FastAPI backend, Next.js frontend, OpenAI integration, and Supabase for storage/authentication.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication
All protected endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

#### POST /api/auth/login
Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

#### POST /api/auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "refresh-token"
}
```

#### POST /api/auth/logout
Logout user and invalidate tokens.

#### POST /api/auth/forgot-password
Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

#### POST /api/auth/reset-password
Reset password using reset token.

**Request Body:**
```json
{
  "token": "reset-token",
  "new_password": "newpassword123"
}
```

### User Management Endpoints

#### GET /api/user/profile
Get current user profile.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### PUT /api/user/profile
Update user profile.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe"
}
```

#### DELETE /api/user/account
Delete user account.

### Task Management Endpoints

#### GET /api/tasks/
Get all tasks for the current user.

**Query Parameters:**
- `status`: Filter by status (pending, in_progress, completed)
- `priority`: Filter by priority (low, medium, high)
- `due_date`: Filter by due date (YYYY-MM-DD)
- `limit`: Number of tasks to return (default: 50)
- `offset`: Number of tasks to skip (default: 0)

**Response:**
```json
{
  "tasks": [
    {
      "id": "uuid",
      "title": "Complete project",
      "description": "Finish the project documentation",
      "status": "pending",
      "priority": "high",
      "due_date": "2024-01-15T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/tasks/
Create a new task.

**Request Body:**
```json
{
  "title": "Complete project",
  "description": "Finish the project documentation",
  "status": "pending",
  "priority": "high",
  "due_date": "2024-01-15T00:00:00Z"
}
```

#### GET /api/tasks/{task_id}
Get a specific task by ID.

#### PUT /api/tasks/{task_id}
Update a task.

**Request Body:**
```json
{
  "title": "Updated task title",
  "description": "Updated description",
  "status": "in_progress",
  "priority": "medium",
  "due_date": "2024-01-20T00:00:00Z"
}
```

#### DELETE /api/tasks/{task_id}
Delete a task.

### Goal Management Endpoints

#### GET /api/goals/
Get all goals for the current user.

**Query Parameters:**
- `status`: Filter by status (active, completed, archived)
- `category`: Filter by category
- `limit`: Number of goals to return (default: 50)
- `offset`: Number of goals to skip (default: 0)

**Response:**
```json
{
  "goals": [
    {
      "id": "uuid",
      "title": "Learn Python",
      "description": "Master Python programming",
      "category": "learning",
      "status": "active",
      "target_date": "2024-06-01T00:00:00Z",
      "progress": 75,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/goals/
Create a new goal.

**Request Body:**
```json
{
  "title": "Learn Python",
  "description": "Master Python programming",
  "category": "learning",
  "target_date": "2024-06-01T00:00:00Z"
}
```

#### GET /api/goals/{goal_id}
Get a specific goal by ID.

#### PUT /api/goals/{goal_id}
Update a goal.

#### DELETE /api/goals/{goal_id}
Delete a goal.

### Schedule Block Endpoints

#### GET /api/schedule-blocks/
Get all schedule blocks for the current user.

**Query Parameters:**
- `date`: Filter by date (YYYY-MM-DD)
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `type`: Filter by block type (focus, break, meeting)
- `limit`: Number of blocks to return (default: 50)
- `offset`: Number of blocks to skip (default: 0)

**Response:**
```json
{
  "schedule_blocks": [
    {
      "id": "uuid",
      "title": "Deep Work Session",
      "description": "Focus on coding",
      "start_time": "2024-01-01T09:00:00Z",
      "end_time": "2024-01-01T11:00:00Z",
      "type": "focus",
      "priority": "high",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/schedule-blocks/
Create a new schedule block.

**Request Body:**
```json
{
  "title": "Deep Work Session",
  "description": "Focus on coding",
  "start_time": "2024-01-01T09:00:00Z",
  "end_time": "2024-01-01T11:00:00Z",
  "type": "focus",
  "priority": "high"
}
```

#### GET /api/schedule-blocks/{block_id}
Get a specific schedule block by ID.

#### PUT /api/schedule-blocks/{block_id}
Update a schedule block.

#### DELETE /api/schedule-blocks/{block_id}
Delete a schedule block.

### Habit Tracking Endpoints

#### GET /api/habits/
Get all habits for the current user.

**Response:**
```json
{
  "habits": [
    {
      "id": "uuid",
      "name": "Daily Exercise",
      "description": "30 minutes of exercise",
      "frequency": "daily",
      "target_count": 1,
      "current_streak": 5,
      "longest_streak": 10,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /api/habits/
Create a new habit.

**Request Body:**
```json
{
  "name": "Daily Exercise",
  "description": "30 minutes of exercise",
  "frequency": "daily",
  "target_count": 1
}
```

#### POST /api/habits/{habit_id}/log
Log a habit completion.

**Request Body:**
```json
{
  "date": "2024-01-01",
  "notes": "Great workout session"
}
```

#### GET /api/habits/{habit_id}
Get a specific habit by ID.

#### PUT /api/habits/{habit_id}
Update a habit.

#### DELETE /api/habits/{habit_id}
Delete a habit.

### AI Integration Endpoints

#### POST /api/ai/generate-task
Generate task suggestions using AI.

**Request Body:**
```json
{
  "prompt": "I need to organize my workspace",
  "context": "I'm a software developer working from home"
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "title": "Organize desk setup",
      "description": "Clean desk, organize cables, set up ergonomic workspace",
      "priority": "medium",
      "estimated_duration": 30
    }
  ],
  "tokens_used": 150,
  "cost": 0.002
}
```

#### POST /api/ai/optimize-schedule
Get AI-powered schedule optimization suggestions.

**Request Body:**
```json
{
  "tasks": [
    {
      "title": "Code review",
      "priority": "high",
      "estimated_duration": 60
    }
  ],
  "preferences": {
    "focus_hours": "09:00-12:00",
    "break_duration": 15
  }
}
```

#### POST /api/ai/analyze-productivity
Get AI analysis of productivity patterns.

**Request Body:**
```json
{
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

### Analytics Endpoints

#### GET /api/analytics/productivity-score
Get user's productivity score.

**Query Parameters:**
- `date_range`: Date range for analysis (e.g., "7d", "30d", "90d")

**Response:**
```json
{
  "score": 85,
  "trend": "increasing",
  "factors": {
    "task_completion": 90,
    "focus_time": 80,
    "goal_progress": 85
  },
  "period": "last_7_days"
}
```

#### GET /api/analytics/task-stats
Get task completion statistics.

**Response:**
```json
{
  "total_tasks": 50,
  "completed_tasks": 35,
  "pending_tasks": 10,
  "overdue_tasks": 5,
  "completion_rate": 70,
  "by_priority": {
    "high": 15,
    "medium": 20,
    "low": 15
  }
}
```

#### GET /api/analytics/focus-time
Get focus time analytics.

**Response:**
```json
{
  "total_focus_time": 120,
  "average_session_length": 45,
  "sessions_count": 8,
  "productivity_score": 85,
  "by_day": {
    "monday": 30,
    "tuesday": 25,
    "wednesday": 35,
    "thursday": 20,
    "friday": 10
  }
}
```

#### GET /api/analytics/productivity-patterns
Get productivity pattern analysis.

**Response:**
```json
{
  "peak_hours": ["09:00", "14:00"],
  "low_energy_hours": ["15:00", "16:00"],
  "best_days": ["tuesday", "wednesday"],
  "recommendations": [
    "Schedule important tasks between 9-11 AM",
    "Take breaks during 3-4 PM low energy period"
  ]
}
```

#### GET /api/analytics/weekly-review
Get weekly productivity review.

**Response:**
```json
{
  "week_start": "2024-01-01",
  "week_end": "2024-01-07",
  "tasks_completed": 25,
  "goals_progress": 3,
  "focus_time": 28,
  "productivity_score": 82,
  "highlights": [
    "Completed major project milestone",
    "Maintained consistent focus sessions"
  ],
  "areas_for_improvement": [
    "Reduce meeting time",
    "Increase deep work sessions"
  ]
}
```

#### GET /api/analytics/trends
Get productivity trends over time.

**Query Parameters:**
- `metric`: Metric to analyze (productivity_score, focus_time, task_completion)
- `period`: Time period (7d, 30d, 90d)

**Response:**
```json
{
  "metric": "productivity_score",
  "period": "30d",
  "trend": "increasing",
  "data": [
    {"date": "2024-01-01", "value": 75},
    {"date": "2024-01-02", "value": 78},
    {"date": "2024-01-03", "value": 82}
  ],
  "change_percentage": 9.3
}
```

### Flashcard Endpoints

#### GET /api/flashcards/
Get all flashcards for the current user.

**Query Parameters:**
- `category`: Filter by category
- `difficulty`: Filter by difficulty (easy, medium, hard)
- `limit`: Number of cards to return (default: 50)
- `offset`: Number of cards to skip (default: 0)

**Response:**
```json
{
  "flashcards": [
    {
      "id": "uuid",
      "front": "What is Python?",
      "back": "A high-level programming language",
      "category": "programming",
      "difficulty": "easy",
      "last_reviewed": "2024-01-01T00:00:00Z",
      "next_review": "2024-01-03T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/flashcards/
Create a new flashcard.

**Request Body:**
```json
{
  "front": "What is Python?",
  "back": "A high-level programming language",
  "category": "programming",
  "difficulty": "easy"
}
```

#### GET /api/flashcards/{card_id}
Get a specific flashcard by ID.

#### PUT /api/flashcards/{card_id}
Update a flashcard.

#### DELETE /api/flashcards/{card_id}
Delete a flashcard.

#### POST /api/flashcards/{card_id}/review
Log a flashcard review.

**Request Body:**
```json
{
  "difficulty": "easy",
  "notes": "Remembered easily"
}
```

### Notification Endpoints

#### GET /api/notifications/
Get all notifications for the current user.

**Query Parameters:**
- `read`: Filter by read status (true/false)
- `type`: Filter by notification type
- `limit`: Number of notifications to return (default: 50)
- `offset`: Number of notifications to skip (default: 0)

**Response:**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "title": "Task Due Soon",
      "message": "Your task 'Complete project' is due in 2 hours",
      "type": "task_reminder",
      "read": false,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/notifications/{notification_id}/read
Mark notification as read.

#### DELETE /api/notifications/{notification_id}
Delete a notification.

### Calendar Integration Endpoints

#### GET /api/calendar/events
Get calendar events.

**Query Parameters:**
- `start_date`: Start date for events
- `end_date`: End date for events
- `type`: Filter by event type

#### POST /api/calendar/events
Create a calendar event.

#### PUT /api/calendar/events/{event_id}
Update a calendar event.

#### DELETE /api/calendar/events/{event_id}
Delete a calendar event.

### Notion Integration Endpoints

#### GET /api/notion/pages
Get Notion pages.

#### POST /api/notion/sync
Sync data with Notion.

#### GET /api/notion/status
Get Notion integration status.

### User Settings Endpoints

#### GET /api/user/settings
Get user settings.

**Response:**
```json
{
  "theme": "dark",
  "notifications": {
    "email": true,
    "push": true,
    "task_reminders": true
  },
  "productivity": {
    "focus_duration": 25,
    "break_duration": 5,
    "long_break_duration": 15
  },
  "privacy": {
    "data_sharing": false,
    "analytics": true
  }
}
```

#### PUT /api/user/settings
Update user settings.

**Request Body:**
```json
{
  "theme": "dark",
  "notifications": {
    "email": true,
    "push": false
  },
  "productivity": {
    "focus_duration": 30,
    "break_duration": 10
  }
}
```

### Privacy Endpoints

#### GET /api/privacy/data
Get user's data export.

#### DELETE /api/privacy/data
Delete user's data.

#### GET /api/privacy/analytics
Get privacy analytics settings.

### Monitoring Endpoints

#### GET /api/metrics
Get application metrics (Prometheus format).

#### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "openai": "healthy"
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details"
  }
}
```

### Common Error Codes
- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Authentication required
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `422`: Validation Error - Invalid request body
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error

## Rate Limiting
- Default: 100 requests per minute per user
- AI endpoints: 10 requests per minute per user
- Authentication endpoints: 5 requests per minute per IP

## Pagination
Endpoints that return lists support pagination with `limit` and `offset` query parameters.

## WebSocket Endpoints

### /ws/notifications
Real-time notification updates.

**Message Format:**
```json
{
  "type": "notification",
  "data": {
    "id": "uuid",
    "title": "New notification",
    "message": "Notification message"
  }
}
```

## SDKs and Libraries
- JavaScript/TypeScript: Available via npm
- Python: Available via pip
- Mobile SDKs: iOS and Android SDKs available

## Support
For API support and questions:
- Email: api-support@cognie.com
- Documentation: https://docs.cognie.com
- Status page: https://status.cognie.com

## Notion Webhook Endpoints

### Webhook Verification

#### GET /api/notion/webhook/notion/verify
Verify Notion webhook subscription.

**Query Parameters:**
- `challenge`: Challenge string from Notion

**Response:**
```json
{
  "challenge": "challenge_string_from_notion"
}
```

### Receive Notion Webhooks

#### POST /api/notion/webhook/notion
Receive webhooks from Notion when pages/databases change.

**Headers:**
- `X-Notion-Signature`: HMAC-SHA256 signature (optional for testing)
- `X-Notion-Timestamp`: Webhook timestamp

**Request Body:**
```json
{
  "type": "page.updated",
  "page": {
    "id": "page-uuid",
    "last_edited_time": "2024-01-01T12:00:00Z"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Webhook processed"
}
```

### Internal Sync Endpoint

#### POST /api/notion/internal/sync
Internal endpoint for processing queued sync operations from webhooks.

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "page_id": "page-uuid",
  "last_edited_time": "2024-01-01T12:00:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "items_synced": 5
}
```

## Analytics Endpoints

### Get Productivity Analytics

#### GET /api/analytics/productivity
Get productivity analytics for the authenticated user.

**Query Parameters:**
- `start_date` (optional): Start date for analytics period
- `end_date` (optional): End date for analytics period
- `group_by` (optional): Group by day, week, or month

**Response:**
```json
{
  "productivity_score": 85.5,
  "tasks_completed": 25,
  "total_tasks": 30,
  "focus_time_hours": 12.5,
  "productivity_trend": [
    {
      "date": "2024-01-01",
      "score": 80,
      "tasks_completed": 5,
      "focus_time": 2.5
    }
  ],
  "top_categories": [
    {
      "category": "work",
      "tasks_completed": 15,
      "productivity_score": 90
    }
  ]
}
```

### Get Goal Analytics

#### GET /api/analytics/goals
Get goal progress analytics.

**Response:**
```json
{
  "total_goals": 5,
  "active_goals": 3,
  "completed_goals": 1,
  "average_progress": 65.5,
  "goals_by_category": [
    {
      "category": "learning",
      "count": 2,
      "average_progress": 75
    }
  ],
  "recent_progress": [
    {
      "goal_id": "goal-uuid",
      "title": "Learn Python",
      "progress": 80,
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### Get Habit Analytics

#### GET /api/analytics/habits
Get habit tracking analytics.

**Response:**
```json
{
  "total_habits": 3,
  "active_habits": 2,
  "current_streaks": [
    {
      "habit_id": "habit-uuid",
      "name": "Daily Exercise",
      "current_streak": 7,
      "longest_streak": 15
    }
  ],
  "completion_rates": [
    {
      "habit_id": "habit-uuid",
      "name": "Daily Exercise",
      "completion_rate": 85.7,
      "total_entries": 30
    }
  ]
}
```

## Schedule Management Endpoints

### Get Schedule Blocks

#### GET /api/schedule-blocks
Get user's schedule blocks.

**Query Parameters:**
- `date` (optional): Filter by specific date
- `start_date` (optional): Start date range
- `end_date` (optional): End date range

**Response:**
```json
{
  "schedule_blocks": [
    {
      "id": "block-uuid",
      "title": "Work Session",
      "start_time": "2024-01-01T09:00:00Z",
      "end_time": "2024-01-01T12:00:00Z",
      "category": "work",
      "priority": "high",
      "status": "scheduled",
      "created_at": "2024-01-01T08:00:00Z"
    }
  ],
  "total": 1
}
```

### Create Schedule Block

#### POST /api/schedule-blocks
Create a new schedule block.

**Request Body:**
```json
{
  "title": "Work Session",
  "start_time": "2024-01-01T09:00:00Z",
  "end_time": "2024-01-01T12:00:00Z",
  "category": "work",
  "priority": "high",
  "description": "Focus on project tasks"
}
```

**Response:**
```json
{
  "id": "block-uuid",
  "title": "Work Session",
  "start_time": "2024-01-01T09:00:00Z",
  "end_time": "2024-01-01T12:00:00Z",
  "category": "work",
  "priority": "high",
  "status": "scheduled",
  "description": "Focus on project tasks",
  "created_at": "2024-01-01T08:00:00Z"
}
```

### Update Schedule Block

#### PUT /api/schedule-blocks/{block_id}
Update an existing schedule block.

**Request Body:**
```json
{
  "title": "Updated Work Session",
  "status": "in_progress"
}
```

**Response:**
```json
{
  "id": "block-uuid",
  "title": "Updated Work Session",
  "start_time": "2024-01-01T09:00:00Z",
  "end_time": "2024-01-01T12:00:00Z",
  "category": "work",
  "priority": "high",
  "status": "in_progress",
  "description": "Focus on project tasks",
  "created_at": "2024-01-01T08:00:00Z",
  "updated_at": "2024-01-01T09:30:00Z"
}
```

### Delete Schedule Block

#### DELETE /api/schedule-blocks/{block_id}
Delete a schedule block.

**Response:**
```json
{
  "message": "Schedule block deleted successfully"
}
```

## Habit Tracking Endpoints

### Get Habits

#### GET /api/habits
Get user's habits.

**Response:**
```json
{
  "habits": [
    {
      "id": "habit-uuid",
      "name": "Daily Exercise",
      "description": "30 minutes of physical activity",
      "frequency": "daily",
      "target_count": 1,
      "current_streak": 7,
      "longest_streak": 15,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1
}
```

### Create Habit

#### POST /api/habits
Create a new habit.

**Request Body:**
```json
{
  "name": "Daily Exercise",
  "description": "30 minutes of physical activity",
  "frequency": "daily",
  "target_count": 1,
  "reminder_time": "18:00"
}
```

**Response:**
```json
{
  "id": "habit-uuid",
  "name": "Daily Exercise",
  "description": "30 minutes of physical activity",
  "frequency": "daily",
  "target_count": 1,
  "current_streak": 0,
  "longest_streak": 0,
  "reminder_time": "18:00",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Log Habit Entry

#### POST /api/habits/{habit_id}/log
Log a habit completion.

**Request Body:**
```json
{
  "date": "2024-01-01",
  "notes": "Great workout session"
}
```

**Response:**
```json
{
  "id": "entry-uuid",
  "habit_id": "habit-uuid",
  "date": "2024-01-01",
  "notes": "Great workout session",
  "created_at": "2024-01-01T18:00:00Z"
}
```

### Update Habit

#### PUT /api/habits/{habit_id}
Update an existing habit.

**Request Body:**
```json
{
  "name": "Updated Habit Name",
  "frequency": "weekly",
  "target_count": 3
}
```

**Response:**
```json
{
  "id": "habit-uuid",
  "name": "Updated Habit Name",
  "description": "30 minutes of physical activity",
  "frequency": "weekly",
  "target_count": 3,
  "current_streak": 7,
  "longest_streak": 15,
  "reminder_time": "18:00",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T13:00:00Z"
}
```

### Delete Habit

#### DELETE /api/habits/{habit_id}
Delete a habit.

**Response:**
```json
{
  "message": "Habit deleted successfully"
}
```

## Flashcard Endpoints

### Get Flashcards

#### GET /api/flashcards
Get user's flashcards.

**Query Parameters:**
- `category` (optional): Filter by category
- `difficulty` (optional): Filter by difficulty
- `page` (optional): Page number for pagination
- `limit` (optional): Number of items per page

**Response:**
```json
{
  "flashcards": [
    {
      "id": "flashcard-uuid",
      "question": "What is the capital of France?",
      "answer": "Paris",
      "category": "geography",
      "difficulty": "medium",
      "last_reviewed": "2024-01-01T12:00:00Z",
      "next_review": "2024-01-03T12:00:00Z",
      "review_count": 5,
      "mastery_level": 0.8,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

### Create Flashcard

#### POST /api/flashcards
Create a new flashcard.

**Request Body:**
```json
{
  "question": "What is the capital of France?",
  "answer": "Paris",
  "category": "geography",
  "difficulty": "medium",
  "tags": ["europe", "capitals"]
}
```

**Response:**
```json
{
  "id": "flashcard-uuid",
  "question": "What is the capital of France?",
  "answer": "Paris",
  "category": "geography",
  "difficulty": "medium",
  "tags": ["europe", "capitals"],
  "last_reviewed": null,
  "next_review": "2024-01-01T12:00:00Z",
  "review_count": 0,
  "mastery_level": 0,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Review Flashcard

#### POST /api/flashcards/{flashcard_id}/review
Review a flashcard and update its mastery level.

**Request Body:**
```json
{
  "rating": 4,
  "notes": "Easy to remember"
}
```

**Response:**
```json
{
  "id": "review-uuid",
  "flashcard_id": "flashcard-uuid",
  "rating": 4,
  "notes": "Easy to remember",
  "mastery_level": 0.8,
  "next_review": "2024-01-03T12:00:00Z",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Update Flashcard

#### PUT /api/flashcards/{flashcard_id}
Update an existing flashcard.

**Request Body:**
```json
{
  "question": "Updated question?",
  "answer": "Updated answer",
  "difficulty": "hard"
}
```

**Response:**
```json
{
  "id": "flashcard-uuid",
  "question": "Updated question?",
  "answer": "Updated answer",
  "category": "geography",
  "difficulty": "hard",
  "tags": ["europe", "capitals"],
  "last_reviewed": "2024-01-01T12:00:00Z",
  "next_review": "2024-01-03T12:00:00Z",
  "review_count": 5,
  "mastery_level": 0.8,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T13:00:00Z"
}
```

### Delete Flashcard

#### DELETE /api/flashcards/{flashcard_id}
Delete a flashcard.

**Response:**
```json
{
  "message": "Flashcard deleted successfully"
}
```

## User Settings Endpoints

### Get User Settings

#### GET /api/user-settings
Get user's settings and preferences.

**Response:**
```json
{
  "user_id": "user-uuid",
  "theme": "dark",
  "language": "en",
  "timezone": "UTC",
  "notifications": {
    "email": true,
    "push": true,
    "reminders": true
  },
  "privacy": {
    "profile_visibility": "private",
    "data_sharing": false
  },
  "notion_api_key": "secret_...",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Update User Settings

#### PUT /api/user-settings
Update user's settings.

**Request Body:**
```json
{
  "theme": "light",
  "notifications": {
    "email": false,
    "push": true,
    "reminders": true
  }
}
```

**Response:**
```json
{
  "user_id": "user-uuid",
  "theme": "light",
  "language": "en",
  "timezone": "UTC",
  "notifications": {
    "email": false,
    "push": true,
    "reminders": true
  },
  "privacy": {
    "profile_visibility": "private",
    "data_sharing": false
  },
  "notion_api_key": "secret_...",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T13:00:00Z"
}
```

## AI Endpoints

### Generate AI Insights

#### POST /api/ai/insights
Generate AI-powered insights about user's productivity.

**Request Body:**
```json
{
  "insight_type": "productivity_analysis",
  "time_period": "last_week"
}
```

**Response:**
```json
{
  "insights": [
    {
      "type": "productivity_trend",
      "title": "Productivity Improvement",
      "description": "Your productivity has increased by 15% compared to last week.",
      "confidence": 0.85,
      "recommendations": [
        "Continue your morning routine",
        "Focus on high-priority tasks first"
      ]
    }
  ],
  "generated_at": "2024-01-01T12:00:00Z"
}
```

### Generate Smart Tasks

#### POST /api/ai/generate-tasks
Generate AI-powered task suggestions.

**Request Body:**
```json
{
  "context": "I want to improve my Python skills",
  "timeframe": "next_week",
  "max_tasks": 5
}
```

**Response:**
```json
{
  "tasks": [
    {
      "title": "Complete Python basics course",
      "description": "Finish the first 3 modules of the Python course",
      "estimated_duration": "2 hours",
      "priority": "high",
      "category": "learning",
      "confidence": 0.9
    }
  ],
  "generated_at": "2024-01-01T12:00:00Z"
}
```

### Optimize Schedule

#### POST /api/ai/optimize-schedule
Get AI-powered schedule optimization suggestions.

**Request Body:**
```json
{
  "date": "2024-01-02",
  "tasks": [
    {
      "id": "task-uuid",
      "title": "Work on project",
      "estimated_duration": "4 hours",
      "priority": "high"
    }
  ],
  "constraints": {
    "work_hours": "09:00-17:00",
    "breaks": ["12:00-13:00"]
  }
}
```

**Response:**
```json
{
  "optimized_schedule": [
    {
      "time_slot": "09:00-11:00",
      "task_id": "task-uuid",
      "task_title": "Work on project",
      "reasoning": "High priority task scheduled during peak productivity hours"
    }
  ],
  "productivity_score": 85,
  "generated_at": "2024-01-01T12:00:00Z"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Validation error description",
  "error_code": "VALIDATION_ERROR"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials",
  "error_code": "AUTHENTICATION_ERROR"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions",
  "error_code": "PERMISSION_ERROR"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR"
}
```

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Authentication endpoints**: 5 requests per minute
- **General endpoints**: 60 requests per minute
- **AI endpoints**: 10 requests per minute
- **Webhook endpoints**: No rate limiting (required for real-time processing)

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Pagination

List endpoints support pagination with the following query parameters:

- `page`: Page number (default: 1)
- `limit`: Number of items per page (default: 10, max: 100)

Pagination metadata is included in responses:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 10,
  "pages": 10,
  "has_next": true,
  "has_prev": false
}
```

## WebSocket Endpoints

### Real-time Updates

#### `WS /api/ws/updates`
WebSocket endpoint for real-time updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/updates');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Message Types:**
- `task_created`: New task created
- `task_updated`: Task updated
- `goal_progress`: Goal progress update
- `habit_logged`: Habit completion logged
- `flashcard_reviewed`: Flashcard reviewed

**Example Message:**
```json
{
  "type": "task_created",
  "data": {
    "id": "task-uuid",
    "title": "New Task",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

## Testing

### Test Endpoints

#### `GET /api/test/health`
Health check for testing purposes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### `POST /api/test/webhook`
Test webhook endpoint for development.

**Request Body:**
```json
{
  "type": "test",
  "data": "test_data"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Test webhook processed"
}
```

## SDK and Libraries

### Python SDK
```python
from cognie import CognieClient

client = CognieClient(api_key="your_api_key")
tasks = client.tasks.list()
```

### JavaScript SDK
```javascript
import { CognieClient } from '@cognie/sdk';

const client = new CognieClient({ apiKey: 'your_api_key' });
const tasks = await client.tasks.list();
```

### cURL Examples

#### Create a task
```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project",
    "priority": "high"
  }'
```

#### Get analytics
```bash
curl -X GET "http://localhost:8000/api/analytics/productivity" \
  -H "Authorization: Bearer your_jwt_token"
```

#### Generate flashcards
```bash
curl -X POST "http://localhost:8000/api/notion/generate-flashcards" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "page-uuid",
    "count": 5
  }'
```

## Support

For API support and questions:

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/cognie/issues)
- **Email**: api-support@cognie.com

---

**API Version**: 1.0.0  
**Last Updated**: January 2024 
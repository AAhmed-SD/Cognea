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
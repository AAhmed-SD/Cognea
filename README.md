# AI Personal Scheduler Agent

> The smart planner that adapts to your brain — not the other way around.

An AI-powered productivity assistant that auto-plans your schedule, reschedules missed tasks, and helps you remember what matters. Built for students, founders, and creators juggling complex lives.

💡 What Cognie Does That Others Don't
✅ Adapts over time to your energy levels and routines
✅ Auto-prioritizes based on your goals (e.g. "Revise for exam")
✅ Reschedules missed tasks with logic — not shame
✅ Tracks memory retention + flashcards + reviews
✅ Understands time constraints, attention span, & task difficulty
✅ Feels like a coach, not a tool

That's rare. Right now, people stitch together:

Notion + ChatGPT + Google Calendar + Quizlet + productivity blogs

You're offering a 1-stop cognitive productivity brain.

---

## 🚀 MVP Feature Set

### 🗓️ 1. Smart Time Blocking
- Auto-generate weekly and daily timeblocks based on priority, duration, and availability
- Respect fixed events (calendar entries, working hours)
- Support manual overrides and visual editing

### 🎯 2. Goal-Aligned Task Planning
- Link tasks to custom goals (e.g. "Launch SaaS", "MSc Revision")
- Visualize progress and task clusters by goal

### 🔁 3. Dynamic Rescheduling
- Detect missed or incomplete tasks
- Automatically re-slot based on urgency, time, and energy level
- Alert if rescheduled too often (suggest deletion or re-scoping)

### 📅 4. Multi-Context Calendar View
- Color-coded task types (Work, Gym, Study, Personal)
- Toggle context layers on/off
- Switch between "Focus View" (1 week) and "Horizon View" (6 months)

### 🧠 5. AI-Powered Daily Brief
- Morning rundown of today's key tasks, focus theme, and any overdue items
- Optional reflection prompt or quote

### 🧩 6. Notion Sync (Basic)
- Push tasks into Notion database or pull task lists via API

---

## 🛠️ Full Feature List (MVP + Future)

### ✅ Core Engine
- Task CRUD system
- User-defined categories (goal, energy level, time estimate)
- Smart scheduler algorithm

### 🔗 Integrations
- Google Calendar sync
- Notion API (basic syncing)
- Stripe subscription billing
- OpenAI for brief/summary generation

### 📊 Analytics & Self-Awareness
- Weekly "You Insights" (e.g. "You overbooked Tuesdays")
- Missed task streak tracker
- Suggested improvements based on user patterns

### 🔄 Memory-Aware Reviews
- Schedule spaced repetition for cognitively Increases odor later (ironically)heavy tasks
- Flashcard-style recall or summary prompts

### 🧘 Personalisation Features
- Define personal focus hours (e.g. "No deep work after 6PM")
- Auto-balance task types (e.g. 40% deep, 60% shallow)
- Energy-based time allocation

---

## 💡 Stretch Features (Post-MVP)
- Voice-activated scheduling (via Whisper or VAPI)
- WhatsApp/Telegram integration
- Machine learning: detect burnout patterns and suggest rest windows
- AI-generated weekly performance reviews
- Shareable "routine templates" from power users

---

## 💸 Pricing Strategy
- **Free**: Task manager + calendar sync
- **£5.99/mo**: AI briefings, smart rescheduling, insights, memory recall
- **£30 LTD**: Early adopters get lifetime access

---

## 🧠 Positioning
**Tagline:** "Schedule smarter. Learn faster. Forget less."

**One-liner pitch:** "The AI planner that adapts to your brain — not the other way around."

**Ideal users:**
- Students with chaotic routines
- Solo founders balancing multiple roles
- Productivity nerds burnt out from Notion overload
- Neurodiverse learners needing extra recall

---

## Additional Features for Study and Learning

1. **📚 Textbook Parsing**
   - **Purpose:** Automatically break down textbooks into manageable study units.

2. **✍️ Q&A Creation**
   - **Purpose:** Allow users to create manual and AI-generated flashcards for each topic.

3. **⏱ Exam-Aware Scheduler**
   - **Purpose:** Build a revision plan based on exam deadlines.

4. **📈 Weak Point Detection**
   - **Purpose:** Use AI to track skipped or incorrect tasks, identifying areas for improvement.

5. **🔁 Spaced Repetition**
   - **Purpose:** Implement a built-in review queue for active recall.

6. **🧠 AI Memory Coach**
   - **Purpose:** Suggest study cycles based on memory retention data.

7. **🗓 Dynamic Calendar Sync**
   - **Purpose:** Integrate the study plan with the user's life calendar, including other commitments.

---

## 🧠 COGNIE – Full Feature List (2025)

### 🔗 Notion Integration
- Embed Notion pages directly into the dashboard
- Sync tasks and notes from Notion into the app
- Convert Notion notes into flashcards or tasks
- AI reads Notion pages for context-aware suggestions

### 🗓️ AI-Powered Scheduling & Time Blocking
- Smart weekly/daily planner (auto time-blocked from priorities)
- One-click "Plan My Day/Week" button using AI
- Auto-prioritization based on urgency, task type, and deadlines
- Time-flexible vs. time-fixed task distinction
- Rescheduling suggestions with drag-and-drop
- Integration with Google Calendar (optional)

### 📋 Task Management
- Add tasks manually or import from Notion
- Status labels (To Do, In Progress, Done)
- Tags, priority levels, and deadlines
- Repeat tasks & habit-style recurring to-dos

### 🧠 Memory Engine (Flashcard System)
- Convert notes or tasks into flashcards
- Spaced repetition & quiz mode (Quizlet-inspired)
- AI-generated questions from text
- Tag-based decks (subject, topic, etc.)
- Progress tracking by topic

### ⏱️ Focus Tools
- Pomodoro & Deep Work timer modes
- Focus mode with distraction blockers
- Ambient sounds / music integration (optional)
- Focus session review (duration, success rate)

### 📊 Gamified Productivity Dashboard
- 🧠 Productivity Score – combines task completion, focus, and consistency
- 🔥 Streaks Tracker – how many days you've stayed consistent
- ⏳ Focus ROI – tracks time spent vs. outcome quality
- 🏆 Achievements – mini milestones like "3-day streak," "10 flashcards done in a day"
- 📈 Trends & Insights – weekly reports and visual stats

### 📎 Knowledge Hub
- Quick Notes space
- AI summary of recent notes or sessions
- Convert written notes → tasks or flashcards

### 🤖 AI Assistant & Recommendations
- AI-generated time plan suggestions
- AI-powered command palette (e.g. "Plan 3 hours of revision this week")
- Personalized productivity tips based on past behavior
- AI recommendations for when to review flashcards

### 📦 Extras / Utility Features
- Light/dark mode toggle
- Sync across devices
- Versioned autosave (rollback possible)
- Smart onboarding flow with quiz to customize experience
- Notion-style clean UI (like Apple meets Superhuman)

### 🎓 Targeted User Features
- **For Students**:
  - Revision planner & flashcards
  - Smart schedule suggestions around study blocks
  - Track grades or test dates (optional)

---

## 🚀 Advanced Feature Set - Future Revenue Expansion

### 📚 Exam-Code Import System
**What the user sees:** Text-box: "Enter AQA-8300-H" → full paper loads in-app in seconds.

**How it works under the hood:** Pre-scraped PDF → parsed into JSON → stored in exam_questions table.

**First-release scope:** AQA GCSE Maths (H) + Edexcel A-Level Biology (Paper 1) only.


### ✍️ AI-Marked Answers
**What the user sees:** Student types or uploads photo; hits Submit → instant mark, model answer & explanation.

**How it works under the hood:** Short answers: regex / numeric range. Essays: GPT-4o with board rubric prompt & temperature 0.

**First-release scope:** Limited to ≤250-word responses; rubric confidence shown (★ rating).


- Tutor partnerships: 30% revenue share

### 📈 Revision Heat-Map
**What the user sees:** Colour grid of syllabus topics: red (weak) → green (strong).

**How it works under the hood:** Aggregates mark data per topic ID; cron job recalculates nightly.

**First-release scope:** Topic summary only; drill questions in v2.



### 🔄 Smart Study Plan Sync
**What the user sees:** Weak topics auto-push into Cognie schedule as spaced-repetition tasks.

**How it works under the hood:** Existing /suggest-reschedule AI endpoint extended to accept weak_topics input.

**First-release scope:** Generates weekly "Past-paper practice" blocks; can be toggled off.


### 👨‍🏫 Teacher / Tutor Dashboard α
**What the user sees:** Class view: student list, average score, weakest topics. CSV export.

**How it works under the hood:** JWT role = teacher; queries student tables; no write actions yet.

**First-release scope:** Read-only; email digest of progress.


### 🏫 School Affiliate Codes
**What the user sees:** Students sign-up with "GREENWOOD-30" → see discount & school crest.

**How it works under the hood:** affiliates table links code → school → commission %. Stripe metadata tags each payment.

**First-release scope:** Flat 30% revenue share, quarterly payout via Stripe Connect.

### Implementation Priority:
1. **Phase 1 (Months 1-3):** AI-Marked Answers, Revision Heat-Map
2. **Phase 2 (Months 4-6):** Exam-Code Import, Smart Study Plan Sync
3. **Phase 3 (Months 7-9):** Teacher Dashboard, School Affiliate Codes

---

## 📧 Weekly Email Progress Reports

- Track user activities such as tasks completed, time spent, and goals achieved.
- Aggregate user data on a weekly basis to generate progress reports.
- Design visually appealing email templates using HTML/CSS.
- Use an email service provider (ESP) like SendGrid, Mailgun, or Amazon SES for email delivery.
- Automate the process of generating and sending emails weekly using a task scheduler.
- Personalize emails with user-specific data to increase engagement.
- Allow users to opt-in or out of receiving weekly progress emails.
- Ensure privacy and security of user data, complying with regulations like GDPR.
- Implement A/B testing and gather feedback to optimize email content.

---

## Real-Time Updates with Notion Webhooks

To enhance the user experience, our application supports real-time updates using Notion webhooks. This feature allows users to receive instant notifications about changes in their Notion workspace, such as updates to pages, databases, or comments.

### Benefits
- **Immediate Feedback**: Users receive instant notifications, helping them stay informed and make timely decisions.
- **Improved Productivity**: Real-time updates help users manage their time more effectively by providing up-to-date information on assignments, deadlines, and other important events.
- **Enhanced Collaboration**: For group projects or shared workspaces, real-time updates ensure that all members are on the same page, reducing miscommunication and improving collaboration.
- **Automation**: Webhooks can trigger automated workflows, such as sending reminders or updating other integrated systems, further streamlining the user's workflow.

### Implementation
To enable real-time updates, we have set up a server to handle incoming webhook requests from Notion. This server processes the events and updates the user's application accordingly. Our system is designed to handle Notion's API rate limits and ensure secure processing of webhook events.

By leveraging Notion webhooks, we aim to provide a seamless and efficient experience for our users, helping them stay organized and productive.

---

## FastAPI Endpoints Plan

### AI Tasks & Memory
- `/generate-flashcards`: Turn raw notes or textbook content into flashcards.
- `/daily-brief`: Generate a daily summary of tasks, priorities, missed tasks, and a reflection.
- `/quiz-me`: Takes a deck ID, returns 3–5 Qs from that deck to quiz the user.
- `/summarize-notes`: Compress long notes into key takeaways.
- `/suggest-reschedule`: Suggest new time + reasoning for missed task.
- `/extract-tasks-from-text`: User brain-dumps a paragraph, AI extracts structured tasks.

### Planning
- `/plan-my-day`: Auto-generate time blocks for a day.
- `/goals`: Create and track high-level goals.
- `/schedule`: Manage scheduled blocks.

### Memory Engine
- flashcards`: CRUD operations for flashcards.
 `/ReviewEngine`
  /review/plan
Purpose: Return a daily personalized review plan.

Input: user_id, available_time, optional exam_date

### Insights
- `/user-insights`: Return trends, missed patterns, overbooking, etc.
- `/ai-feedback`: GPT reviews your week.

### Utility + UX
- `/notifications`: Basic create/delete for reminders.
- `/settings`: Save user energy preferences, focus hours, etc.

### Integration
- `/notion-sync`: Push/pull tasks and notes from Notion.

### Command UX (stretch)
- `/ai-command`: One endpoint for command-palette prompts.

---

## Planned Endpoints

### /review/plan
- **Purpose**: Return a daily personalized review plan.
- **Input**: `user_id`, `available_time`, optional `exam_date`
- **Output**: List of flashcards scheduled for review today, prioritized by difficulty and urgency.

### /review/update
- **Purpose**: Log the outcome of a flashcard review.
- **Input**: `flashcard_id`, `was_correct`
- **Output**: Updated review performance metrics

---

Let me know if you want this synced into your GitHub README or styled for a product landing page.

# Personal Agent API

A FastAPI backend for personal productivity and habits tracking.

## Features

- Diary/Journal entries
- Habits & Routines tracking
- Mood & Emotion tracking
- Analytics & Trends
- Adaptive Profile & Preferences
- Privacy & Data Management
- AI & Personalization
- Fitness Sync
- Calendar Sync
- Notion Sync

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set environment variables:
   ```
   export DISABLE_RATE_LIMIT=true  # Optional: Disable rate limiting
   ```
4. Run the app:
   ```
   uvicorn main:app --reload
   ```

## API Documentation

Once the app is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests with pytest:
```
pytest
```

# Authentication, Token Storage, and Feature Enforcement

## Authentication
- JWT/OAuth authentication is implemented using FastAPI Users and python-jose.
- Endpoints for login, token generation, and token validation are available at `/auth/jwt/login`, `/auth/jwt/refresh`, etc.

## Token Storage
- Tokens are stored securely in the database using SQLAlchemy.

## Per-User Feature Enforcement
- Endpoints are protected using a dependency that checks the user's enabled features before allowing access.

## Celery for Token Refresh
- Celery is set up for background token refresh tasks.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set up your database (PostgreSQL recommended).
3. Run database migrations.
4. Start the FastAPI app: `uvicorn main:app --reload`
5. Start the Celery worker: `celery -A app.celery_app worker --loglevel=info`

# Onboarding & Operations Quick Reference

## Run Tests

```bash
pytest tests/
```

## Run DB Migrations (after any model change)

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## Back Up the Database

- **Postgres:**
  ```bash
  pg_dump your_db > /backups/backup_$(date +%F).sql
  ```
- **SQLite:**
  ```bash
  cp /path/to/your_db.sqlite /backups/backup_$(date +%F).sqlite
  ```

## Restore the Database

- **Postgres:**
  ```bash
  psql your_db < /backups/backup_YYYY-MM-DD.sql
  ```
- **SQLite:**
  ```bash
  sqlite3 /path/to/your_db.sqlite < /backups/backup_YYYY-MM-DD.sqlite
  ```

## Best Practices
- Add a test for every new/changed endpoint in `tests/`
- Run Alembic migrations after every model change
- Schedule regular DB backups (cron job or CI/CD)
- Only document what's needed for onboarding and ops

## 🛠️ Technical Architecture

## 🚩 Feature Flag System

The application implements a robust feature flag system that enables controlled feature rollouts and A/B testing. This system is particularly useful for:
- Gradual feature rollouts to specific user segments
- A/B testing new features
- Managing feature availability based on user types (e.g., students vs. regular users)
- Time-based feature releases

### Key Features
- **Percentage-based Rollouts**: Gradually release features to a percentage of users
- **User Type Targeting**: Enable features for specific user segments (e.g., students)
- **Time-based Availability**: Schedule feature releases and end dates
- **Global & User-specific Flags**: Control features at both global and individual user levels
- **Complex Conditions**: Support for advanced feature availability rules

### Usage Example
```python
# Create a new feature flag
feature_flag = FeatureFlagService.create_feature_flag(
    feature_name="new_student_feature",
    description="A new feature for students",
    is_globally_enabled=True,
    rollout_percentage=50,  # Roll out to 50% of users
    target_user_types=["student"],
    start_date=datetime.utcnow()
)

# Check if a feature is enabled for a user
is_enabled = user.has_feature("new_student_feature")
```

### Implementation Details
- Built on PostgreSQL with JSON support
- Redis caching for performance
- RESTful API endpoints for management
- Real-time feature flag updates
- Comprehensive logging and analytics

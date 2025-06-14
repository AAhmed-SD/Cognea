📝 Diary / Journal
 POST /diary-entry — Create a new diary/journal entry (text, mood, tags, date)

 GET /diary-entries/{user_id} — List all diary entries for a user (filters: date, mood, tag, sentiment)

 GET /diary-entry/{entry_id} — Retrieve a single diary entry

 PUT /diary-entry/{entry_id} — Update a diary entry

 DELETE /diary-entry/{entry_id} — Delete a diary entry

 GET /diary-stats/{user_id} — (Optional) Get mood/sentiment trends over diary entries

 POST /diary-entry/reflect — (Optional) AI-generated reflection prompt based on past week

🔁 Habits & Routines
 POST /habit — Create a new habit/routine (name, frequency, time, energy level, reminder toggle)

 GET /habits/{user_id} — List all habits (filters: category, consistency, streak length)

 PUT /habit/{habit_id} — Update a habit

 DELETE /habit/{habit_id} — Delete a habit

 POST /habit-log — Mark habit as complete

 GET /habit-streaks/{user_id} — View active and historical streaks

 GET /habit-calendar/{user_id} — (Optional) Return heatmap view of completions

 POST /habit/suggest — (Optional) AI suggestion for new habits based on user behavior

😌 Mood & Emotion Tracking
 POST /mood — Log mood (value, timestamp, tags, optional journal)

 GET /moods/{user_id} — List mood logs (filters: time range, intensity)

 GET /mood-stats/{user_id} — Trends: most common moods, mood over time

 POST /mood/prompt — (Optional) Trigger journaling or quote based on mood

 GET /mood-correlations/{user_id} — (Optional) Return correlations with tasks, sleep, focus time, etc.

📈 Analytics & Trends
 GET /analytics/{user_id} — Personalized dashboard (habits, mood, focus time, goals)

 GET /trends/{user_id} — Visual insights over time (calendar heatmap, bar charts)

 GET /weekly-review/{user_id} — (Optional) AI-generated summary of the week

 GET /productivity-patterns/{user_id} — (Optional) Best day/time insights

🧠 Adaptive Profile & Preferences
 PUT /user-profile/{user_id} — Update focus hours, energy curve, goal weightings

 GET /user-profile/{user_id} — Retrieve full adaptive profile

 POST /feedback — Feedback loop (already exists)

 POST /preferences/adjust — (Optional) Auto-tune based on usage (e.g. prefers AM deep work)

🔒 Privacy & Data Management
 POST /export-data/{user_id} — Export all data (GDPR, CSV or JSON)

 DELETE /delete-account/{user_id} — Delete account + anonymize data

 GET /privacy-summary — (Optional) Show user what data is stored

🧠 Optional (Advanced Personalization)
 POST /ai-insights/{user_id} — AI-generated insights & personalized suggestions

 POST /routine-template/{user_id} — Generate/update optimal week schedule

 GET /auto-checkins/{user_id} — (Optional) Daily or weekly prompts for consistency

 POST /trigger-checkin/{user_id} — (Optional) Manual trigger for a check-in via UI

🧩 User Feature Preferences (Modular)
 GET /user/settings/features — Get toggles: flashca

 3. Habit Tracking
 POST /habit — Create a new habit/routine
Input: habit_name, description, frequency, preferred_time, category, reminders_enabled
Output: habit ID + metadata

 GET /habits/{user_id} — List all habits for a user
Filters: category, active/inactive, streaks, tags

 PUT /habit/{habit_id} — Update a habit
Purpose: Edit habit name, frequency, category, etc.

 DELETE /habit/{habit_id} — Delete or archive a habit

 POST /habit-log — Mark a habit as completed
Input: habit_id, timestamp, optional mood, optional notes
Purpose: Used to update habit streaks and completion stats

 GET /habit-streaks/{user_id} — Get habit streak analytics
Output: current streaks, missed days, consistency %

✅ 4. Fitness Sync
 POST /fitness/connect — Connect to fitness service
Input: Auth token or OAuth request
Purpose: Integrate with Apple Health, Google Fit, etc.

 POST /fitness/disconnect — Disconnect integration

 GET /fitness/data — Fetch recent fitness data
Output: Workouts, steps, calories (time-series data)

✅ 5. Calendar & Notion Sync
Calendar Integration

 POST /calendar/connect — Start Google/Apple Calendar sync via OAuth

 GET /calendar/sync — Fetch user events
Filters: busy/free, date range, color

 POST /calendar/push — Push Cognie tasks into calendar

Notion Integration

 POST /notion/connect — Start Notion API integration

 GET /notion/pull-tasks — Import tasks or notes from Notion

 POST /notion/push-tasks — Push tasks or flashcards to Notion

 POST /notion/webhook-handler — Handle updates from Notion in real time

✅ 6. General Recommendations
User Profile/Settings

 GET /user/settings — Retrieve all preferences

 POST /user/settings — Update focus hours, energy curve, enabled modules, default views

Modular API Design

Group routes like /api/diary/, /api/habits/, /api/notion/ etc.

Keep routes RESTful and feature-scoped

Security

Use JWT/OAuth authentication

Protect routes with Depends(get_current_user)

Store tokens encrypted in DB

Set up token refresh with Celery (optional)

## Enterprise Auth & Feature Enforcement TODOs

- [ ] Implement FastAPI Users integration for JWT/OAuth authentication (register, login, token endpoints)
- [ ] Add SQLAlchemy user model and DB migration for persistent token storage
- [ ] Add route protection with Depends(get_current_user) to all routers
- [ ] Implement Celery app and background task for token refresh
- [ ] Add per-user feature enforcement dependency and apply to feature endpoints

*Requirements and code structure are ready, but these features are not yet implemented.*
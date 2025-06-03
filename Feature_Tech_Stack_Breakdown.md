# 🛠️ Feature-by-Feature Tech Stack Breakdown

## 🧠 1. Smart Time Blocking (Scheduling Engine)
**Goal**: Auto-generate weekly/daily schedules based on task data, constraints, and preferences.

**✅ Core Tech**:
- **Scheduling Logic**: Python (custom logic or constraint solver like pulp, optapy, or Google OR-Tools)
- **Time Parsing**: dateutil, pendulum, or Arrow (for timezone-aware time handling)
- **Backend**: FastAPI (REST API endpoints for scheduling input/output)
- **Task Storage**: PostgreSQL or SQLite with sqlmodel or SQLAlchemy
- **Async Tasks**: Celery + Redis (generate schedules in background)
- **Calendar Sync**: Google Calendar API + optional iCal for Apple Calendar
- **Frontend**: React + Tailwind + drag-and-drop UI (e.g. react-beautiful-dnd)

**Optional Enhancements**:
- Use OpenAI or GPT to generate natural-language task descriptions to time-block
- Cache common suggestions with Redis

## 🎯 2. Goal-Aligned Task Planning
**Goal**: Link tasks to broader goals and visualize them.

**✅ Tech**:
- **Goal/Task Models**: PostgreSQL models with ForeignKey relationships
- **Visualization**: Frontend: D3.js or Recharts for goal trees or progress charts
- **UI Tagging**: React + custom dropdown tags, goal progress bars

## 🔁 3. Dynamic Rescheduling
**Goal**: Detect missed tasks and re-slot intelligently.

**✅ Tech**:
- **Background Checks**: Celery beat (periodic task to evaluate missed items)
- **Update Logic**: Custom priority + availability algorithm
- **Notifications**: In-app popups + optional emails via SendGrid or Mailgun

## 📅 4. Multi-Context Calendar View
**Goal**: Show calendar by context (study, work, etc).

**✅ Tech**:
- **Frontend Calendar**: react-big-calendar or FullCalendar
- **Color Layers**: Context tags with predefined color schemes
- **Toggle Views**: React state logic (toggle 1-week vs 6-month)

## 🧠 5. AI-Powered Daily Brief
**Goal**: Generate summaries and to-dos each morning.

**✅ Tech**:
- **NLP**: OpenAI GPT-4-turbo or Claude API
- **Data Source**: Query user task table for the day
- **Delivery**: Rendered as a component + optional email
- **Prompting**: Include tags like urgency, energy, deadline in the prompt context

## 🧩 6. Notion Sync (Basic)
**Goal**: Pull/push tasks to Notion databases.

**✅ Tech**:
- **API**: Notion SDK (@notionhq/client)
- **Sync Logic**: FastAPI endpoint + webhook-based sync
- **Auth**: OAuth2 via Notion developer portal
- **Format Tasks**: Markdown → JSON blocks conversion (for notes or flashcards)

## 🔄 7. Memory Engine (Recall + Flashcards)
**Goal**: Store, embed, and recall memories.

**✅ Tech**:
- **Embeddings**: OpenAI Embeddings (or sentence-transformers locally)
- **Vector Store**: Qdrant or pgvector (PostgreSQL extension)
- **Input Handling**: Notes via text/voice → vectorized
- **Retrieval**: Cosine similarity search + ranked recall

## 📚 8. Textbook Parsing + Q&A Generation
**Goal**: Convert textbooks into learning modules.

**✅ Tech**:
- **Parsing**: pdfplumber, PyMuPDF, or textract
- **Chunking**: Custom splitter based on headings/pages
- **Q&A Gen**: OpenAI GPT prompt chains
- **Flashcard Output**: Stored as JSON or markdown cards with tags

## 📊 9. Analytics + Insights
**Goal**: Weekly trends, overbooking alerts, streaks.

**✅ Tech**:
- **Data Aggregation**: SQL + scheduled batch jobs
- **Trends UI**: Recharts or Chart.js in React
- **Streaks**: Custom logic: compare current vs historical task completion
- **Insight Generation**: GPT prompt: "Summarize this user's week"

## 📧 10. Weekly Email Reports
**Goal**: Send user a personalized snapshot.

**✅ Tech**:
- **Scheduler**: Celery beat (weekly job)
- **HTML Emails**: Jinja2 + MJML or raw HTML templates
- **ESP**: SendGrid, Mailgun, or Amazon SES
- **Personalization**: Dynamic templating + AI summary injection 
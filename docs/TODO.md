# 📝 Comprehensive To-Do List for Cognie

## Environment Setup
- [x] Set up Python virtual environment
- [x] Install necessary Python libraries:
  - [x] OpenAI
  - [x] SQLAlchemy
  - [x] pdfplumber
  - [x] PyMuPDF
  - [x] Qdrant Client

## AI Logic Development
- [ ] Integrate OpenAI API for text generation
- [ ] Develop AI-Powered Daily Brief logic
- [ ] Implement Memory Engine for recall and flashcards
- [ ] Set up Textbook Parsing and Q&A Generation
- [ ] Create Analytics and Insights generation logic

## Backend Development
- [ ] Set up FastAPI for backend services
- [ ] Implement scheduling logic with Python
- [ ] Configure PostgreSQL or SQLite for task storage
- [ ] Set up Celery and Redis for async tasks

## Frontend Development
- [ ] Develop React components for UI
- [ ] Integrate Tailwind CSS for styling
- [ ] Implement drag-and-drop UI with react-beautiful-dnd

## Integration
- [ ] Sync with Google Calendar API
- [ ] Set up Notion Sync using Notion SDK

## Testing and Validation
- [ ] Write test cases for AI logic
- [ ] Validate API endpoints

## Deployment
- [ ] Configure CI/CD pipeline with GitHub Actions
- [ ] Deploy frontend with Vercel or Netlify
- [ ] Deploy backend with Heroku or AWS

## Documentation
- [x] Create Feature-by-Feature Tech Stack Breakdown
- [ ] Document API endpoints and usage

## Additional Tasks
- [ ] Monitor API usage and costs
- [ ] Optimize database queries and indexing
- [ ] Implement caching strategies with Redis
- [ ] Set up monitoring and logging tools

## Future Enhancements
- [ ] Plan for voice scheduling with Whisper
- [ ] Explore additional integrations (e.g., WhatsApp/Telegram)

## Completed Tasks
- Improved error handling in `generate_openai_text` by returning structured error responses.
- Added token usage reporting in the OpenAI integration.
- Enhanced logging granularity with more logging levels.
- Suggested a clean directory structure for separating frontend and backend.

## Next Steps
- Implement the suggested directory structure by moving frontend and backend files into separate directories.
- Test the FastAPI server to ensure it runs without errors after installing missing packages.
- Continue with any remaining tasks on the to-do list, focusing on resolving any blockers and ensuring the application is stable.

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
- `/flashcards`: CRUD operations for flashcards.

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

### /user-insights

#### Database Schema Updates
- Add Context Information:
  - Add a column to the tasks table to store the context of each task (e.g., Work, Study, Personal).
  - Add a column to store the duration of each task.
- Create a New Table (if needed):
  - If tasks are not already stored in a table, create a new table to store task details, including task ID, user ID, context, duration, start time, and end time.

#### Data Collection Logic
- Aggregate Time Spent:
  - Implement a function to calculate the total time spent in each context over a specified period.
  - Use SQL queries to aggregate the data based on the context and time period.
- Calculate Duration:
  - Ensure that the duration of each task is calculated and stored in the database.
  - This can be done by calculating the difference between the start time and end time of each task.

#### Implementation Steps
- Update Database Schema:
  - Modify the existing tasks table or create a new table to include context and duration columns.
- Implement Data Collection Logic:
  - Write SQL queries or ORM methods to aggregate time spent in each context.
  - Implement a function to calculate the total time spent in each context over a specified period.
- Test the Implementation:
  - Validate the accuracy of the aggregated data.
  - Ensure that the duration calculations are correct.
- Integrate with /user-insights Endpoint:
  - Update the /user-insights endpoint to include time allocation data in the response.

---

This checklist will help guide the development process, ensuring all necessary steps are completed efficiently. Each task should be checked off as it is completed to track progress. 
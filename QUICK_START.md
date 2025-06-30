# 🚀 Quick Start Guide - Cognie

Get Cognie running locally in 5 minutes!

## Prerequisites

- Python 3.11+
- Node.js 18+
- Redis server
- Git

## 1. Clone and Setup

```bash
git clone <your-repo-url>
cd personal-agent
```

## 2. Environment Setup

```bash
# Copy environment template
cp env.production.template .env

# Edit .env with your values (see below for required fields)
nano .env
```

### Required Environment Variables

**Minimum setup for local development:**

```bash
# Supabase (get from https://supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_JWT_KEY=your_jwt_secret

# OpenAI (get from https://platform.openai.com)
OPENAI_API_KEY=sk-your_api_key_here

# Security
SECRET_KEY=your_32_character_secret_key_here

# Redis (local)
REDIS_URL=redis://localhost:6379

# Optional: Notion (for full integration)
NOTION_CLIENT_ID=your_notion_client_id
NOTION_CLIENT_SECRET=your_notion_client_secret
NOTION_WEBHOOK_SECRET=your_webhook_secret
```

## 3. Install Dependencies

```bash
# Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Development tools (optional but recommended)
pip install ruff black mypy pre-commit
pre-commit install

# Frontend dependencies
npm install
```

## 4. Database Setup

```bash
# Run database migrations
python setup_supabase_tables.py
```

## 5. Start Services

```bash
# Terminal 1: Start Redis (if not running)
redis-server

# Terminal 2: Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start frontend
npm run dev
```

## 6. Verify Installation

- **Backend API**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

## 🧪 Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=.

# Specific test file
pytest tests/test_notion_webhooks.py -v
```

## 🔧 Development Tools

### Code Formatting
```bash
# Auto-format with black
black .

# Lint with ruff
ruff check .

# Type check with mypy
mypy .
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🚨 Troubleshooting

### Common Issues

**1. Redis Connection Error**
```bash
# Install Redis on macOS
brew install redis

# Install Redis on Ubuntu
sudo apt-get install redis-server

# Start Redis
redis-server
```

**2. Supabase Connection Error**
- Verify your Supabase URL and keys
- Check if your IP is allowed in Supabase dashboard
- Ensure database is running

**3. OpenAI API Error**
- Verify your API key is valid
- Check your OpenAI account has credits
- Ensure you're using the correct model

**4. Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

## 📚 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Test Notion Integration**: Follow the [Notion Setup Guide](docs/NOTION_WEBHOOK_SETUP.md)
3. **Read Documentation**: Check the [docs/](docs/) folder
4. **Join Development**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## 🆘 Need Help?

- **Documentation**: [docs/](docs/)
- **Issues**: Create a GitHub issue
- **Discussions**: Use GitHub discussions

---

**Happy coding! 🎉** 
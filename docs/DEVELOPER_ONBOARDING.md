# Developer Onboarding Guide

Welcome to the Cognie development team! This guide will help you get up and running with the codebase quickly.

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**
- **Node.js 18+**
- **Redis 6+**
- **Git**
- **Docker** (optional but recommended)

### Environment Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/cognie.git
   cd cognie
   ```

2. **Set Up Python Environment**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set Up Node.js Environment**
   ```bash
   npm install
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   # Set up Supabase project and get credentials
   # Update .env with Supabase credentials
   python setup_supabase_tables.py
   ```

6. **Start Development Servers**
   ```bash
   # Terminal 1: Backend
   python main.py
   
   # Terminal 2: Frontend
   npm run dev
   
   # Terminal 3: Redis (if not running)
   redis-server
   ```

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   Redis Cache   │    │   Supabase      │
│   Storage       │    │   & Sessions    │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Background    │    │   OpenAI API    │
                       │   Workers       │    │   (GPT-4)       │
                       └─────────────────┘    └─────────────────┘
```

### Directory Structure

```
cognie/
├── app/                    # Frontend Next.js app
│   ├── components/         # React components
│   ├── models/            # Frontend data models
│   └── services/          # Frontend API services
├── components/            # Shared React components
│   ├── Auth/             # Authentication components
│   ├── Dashboard/        # Dashboard components
│   ├── Layout/           # Layout components
│   └── Payment/          # Payment components
├── config/               # Configuration files
├── contexts/             # React contexts
├── docs/                 # Documentation
├── middleware/           # FastAPI middleware
├── migrations/           # Database migrations
├── models/               # Database models
├── pages/                # Next.js pages
├── public/               # Static assets
├── routes/               # FastAPI route handlers
├── services/             # Backend services
│   ├── ai/               # AI-related services
│   └── notion/           # Notion integration
├── styles/               # CSS styles
├── tests/                # Test files
├── main.py               # FastAPI application entry
├── requirements.txt      # Python dependencies
└── package.json          # Node.js dependencies
```

### Data Flow Architecture

```
User Action → Frontend → API Gateway → Route Handler → Service Layer → Database
     ↑                                                                   ↓
     └─────────────── Response ←─── Cache Layer ←─── Background Jobs ←──┘
```

## 🔧 Development Workflow

### Code Organization

#### Backend (Python/FastAPI)

**Routes** (`routes/`)
- Handle HTTP requests
- Input validation
- Response formatting
- Authentication checks

**Services** (`services/`)
- Business logic
- External API integrations
- Data processing
- Background tasks

**Models** (`models/`)
- Database models
- Data validation
- Relationships
- Migrations

**Middleware** (`middleware/`)
- Authentication
- Rate limiting
- Logging
- Error handling

#### Frontend (Next.js/React)

**Components** (`components/`)
- Reusable UI components
- Feature-specific components
- Layout components

**Pages** (`pages/`)
- Route components
- Page-level logic
- API integration

**Contexts** (`contexts/`)
- Global state management
- Authentication state
- Theme management

**Services** (`services/`)
- API client
- Data fetching
- State management

### Development Guidelines

#### Code Style

**Python**
- Use Black for formatting
- Follow PEP 8 conventions
- Type hints for all functions
- Docstrings for all classes and functions

**JavaScript/React**
- Use Prettier for formatting
- Follow ESLint rules
- Use TypeScript for type safety
- Functional components with hooks

#### Git Workflow

1. **Branch Naming**
   ```
   feature/user-authentication
   bugfix/login-error
   hotfix/security-patch
   ```

2. **Commit Messages**
   ```
   feat: add user authentication system
   fix: resolve login validation error
   docs: update API documentation
   test: add authentication tests
   ```

3. **Pull Request Process**
   - Create feature branch
   - Make changes with tests
   - Update documentation
   - Create PR with description
   - Request code review
   - Merge after approval

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_auth.py

# Run with coverage
python -m pytest --cov=.

# Run frontend tests
npm test
```

### Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_auth.py            # Authentication tests
├── test_tasks.py           # Task management tests
├── test_notion_integration.py  # Notion integration tests
└── test_stripe_integration.py  # Payment tests
```

### Writing Tests

#### Backend Tests
```python
import pytest
from fastapi.testclient import TestClient
from main import app

def test_create_task():
    client = TestClient(app)
    response = client.post(
        "/api/tasks/",
        json={"title": "Test Task", "description": "Test Description"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Task"
```

#### Frontend Tests
```javascript
import { render, screen } from '@testing-library/react';
import Dashboard from '../components/Dashboard/Dashboard';

test('renders dashboard title', () => {
  render(<Dashboard />);
  expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
});
```

## 🔌 API Development

### API Structure

```
/api/
├── auth/           # Authentication endpoints
├── tasks/          # Task management
├── goals/          # Goal tracking
├── schedule/       # Scheduling
├── flashcards/     # Memory engine
├── habits/         # Habit tracking
├── analytics/      # Analytics and insights
├── notion/         # Notion integration
└── stripe/         # Payment processing
```

### API Versioning

Currently using URL versioning:
- `/api/v1/tasks/`
- `/api/v1/goals/`

Future versions will be:
- `/api/v2/tasks/`
- `/api/v2/goals/`

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## 🚀 Deployment

### Development Deployment

```bash
# Build frontend
npm run build

# Start production server
python main.py
```

### Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions.

## 🔍 Debugging

### Backend Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Use FastAPI's built-in debug mode
uvicorn main:app --reload --log-level debug
```

### Frontend Debugging

```javascript
// Use React Developer Tools
// Enable source maps in development
// Use browser dev tools for network requests
```

### Database Debugging

```sql
-- Enable query logging in Supabase
-- Use Supabase dashboard for query analysis
-- Monitor performance with pg_stat_statements
```

## 📚 Learning Resources

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### Next.js
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://reactjs.org/docs/)

### Supabase
- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/)

### Testing
- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

## 🤝 Contributing

### Contribution Guidelines

1. **Fork the Repository**
   - Create your own fork
   - Clone to your local machine

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Write clean, documented code
   - Add tests for new features
   - Update documentation

4. **Test Your Changes**
   ```bash
   python -m pytest
   npm test
   ```

5. **Submit Pull Request**
   - Clear description of changes
   - Link to related issues
   - Request review from team

### Code Review Process

1. **Automated Checks**
   - Linting passes
   - Tests pass
   - Coverage maintained

2. **Manual Review**
   - Code quality
   - Security considerations
   - Performance impact
   - Documentation updates

3. **Approval Process**
   - At least one approval required
   - Address all review comments
   - Merge after approval

### Issue Reporting

When reporting issues:

1. **Use Issue Templates**
   - Bug report template
   - Feature request template
   - Documentation request template

2. **Provide Details**
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment information
   - Screenshots if applicable

## 🆘 Getting Help

### Internal Resources
- **Team Chat**: Slack/Discord channel
- **Code Reviews**: Ask for help during reviews
- **Documentation**: Check existing docs first

### External Resources
- **Stack Overflow**: For general programming questions
- **GitHub Issues**: For project-specific issues
- **Community Forums**: For framework-specific help

## 🎯 Next Steps

1. **Set up your development environment**
2. **Run the test suite**
3. **Make a small contribution**
4. **Join team discussions**
5. **Start working on assigned tasks**

Welcome to the team! 🚀 
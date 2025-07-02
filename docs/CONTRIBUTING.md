# Contributing to Cognie

Thank you for your interest in contributing to Cognie! This document provides guidelines and information for contributors.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Git Workflow](#git-workflow)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Code of Conduct](#code-of-conduct)

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.13+**
- **Node.js 18+**
- **Git**
- **Redis 6+**
- **Docker** (optional but recommended)

### Fork and Clone

1. **Fork the repository**
   - Go to [Cognie Repository](https://github.com/your-username/cognie)
   - Click "Fork" in the top right

2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/cognie.git
   cd cognie
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/original-owner/cognie.git
   ```

## Development Setup

### Environment Setup

1. **Set up Python environment**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up Node.js environment**
   ```bash
   npm install
   ```

3. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database setup**
   ```bash
   # Set up Supabase project and get credentials
   # Update .env with Supabase credentials
   python setup_supabase_tables.py
   ```

### Running the Application

1. **Start development servers**
   ```bash
   # Terminal 1: Backend
   python main.py
   
   # Terminal 2: Frontend
   npm run dev
   
   # Terminal 3: Redis (if not running)
   redis-server
   ```

2. **Verify setup**
   - Backend: http://localhost:8000/docs
   - Frontend: http://localhost:3000
   - Health check: http://localhost:8000/health

## Code Style

### Python Code Style

We follow **PEP 8** and use **Black** for formatting:

```bash
# Install development dependencies
pip install black flake8 isort mypy

# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Linting
flake8 .
```

#### Python Guidelines

- **Type hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all functions and classes
- **Line length**: Maximum 88 characters (Black default)
- **Imports**: Group imports: standard library, third-party, local
- **Naming**: Use snake_case for variables and functions, PascalCase for classes

```python
from typing import Optional, List, Dict, Any
from datetime import datetime

import fastapi
from pydantic import BaseModel

from models.user import User
from services.auth import AuthService


class UserService:
    """Service for user management operations."""
    
    def __init__(self, auth_service: AuthService):
        """Initialize the user service.
        
        Args:
            auth_service: Authentication service instance
        """
        self.auth_service = auth_service
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            User object if found, None otherwise
        """
        # Implementation here
        pass
```

### JavaScript/React Code Style

We use **Prettier** and **ESLint**:

```bash
# Install development dependencies
npm install --save-dev prettier eslint @typescript-eslint/parser

# Format code
npm run format

# Lint code
npm run lint
```

#### JavaScript Guidelines

- **TypeScript**: Use TypeScript for type safety
- **Functional components**: Prefer functional components with hooks
- **Naming**: Use camelCase for variables and functions, PascalCase for components
- **Imports**: Group imports: React, third-party, local

```typescript
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

import { User } from '../types/user';
import { apiService } from '../services/api';

interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ 
  userId, 
  onUpdate 
}) => {
  const [user, setUser] = useState<User | null>(null);
  const { user: currentUser } = useAuth();

  useEffect(() => {
    const fetchUser = async () => {
      const userData = await apiService.getUser(userId);
      setUser(userData);
    };
    
    fetchUser();
  }, [userId]);

  return (
    <div className="user-profile">
      {/* Component JSX */}
    </div>
  );
};
```

## Git Workflow

### Branch Naming Convention

Use descriptive branch names with prefixes:

```
feature/user-authentication
bugfix/login-error
hotfix/security-patch
docs/api-documentation
test/add-auth-tests
refactor/auth-service
```

### Commit Message Format

Follow the **Conventional Commits** specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

#### Examples

```bash
feat: add user authentication system
fix: resolve login validation error
docs: update API documentation
test: add authentication tests
refactor: improve auth service performance
chore: update dependencies
```

### Git Workflow Steps

1. **Create feature branch**
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**
   ```bash
   # Make your changes
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create pull request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the PR template

## Testing

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

# Run tests in watch mode
npm run test:watch
```

### Writing Tests

#### Backend Tests

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app
from services.auth import AuthService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    """Create mock auth service."""
    return Mock(spec=AuthService)


def test_create_user_success(client, mock_auth_service):
    """Test successful user creation."""
    user_data = {
        "email": "test@example.com",
        "password": "securepassword",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    with patch('routes.auth.auth_service', mock_auth_service):
        mock_auth_service.register_user.return_value = {
            "user": {"id": "123", "email": "test@example.com"},
            "message": "User created successfully"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 201
        assert "user" in response.json()
        assert response.json()["user"]["email"] == "test@example.com"
```

#### Frontend Tests

```typescript
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AuthProvider } from '../contexts/AuthContext';
import { LoginForm } from '../components/Auth/LoginForm';

describe('LoginForm', () => {
  it('renders login form', () => {
    render(
      <AuthProvider>
        <LoginForm />
      </AuthProvider>
    );
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('handles form submission', async () => {
    const mockOnSubmit = jest.fn();
    
    render(
      <AuthProvider>
        <LoginForm onSubmit={mockOnSubmit} />
      </AuthProvider>
    );
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' }
    });
    
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' }
    });
    
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    });
  });
});
```

### Test Coverage

We aim for **80%+ test coverage**. Run coverage reports:

```bash
# Backend coverage
python -m pytest --cov=. --cov-report=html

# Frontend coverage
npm run test:coverage
```

## Documentation

### Documentation Standards

- **API Documentation**: Use OpenAPI/Swagger annotations
- **Code Documentation**: Use docstrings and inline comments
- **User Documentation**: Write clear, step-by-step guides
- **Architecture Documentation**: Keep diagrams and design docs updated

### Writing Documentation

#### API Documentation

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class UserCreate(BaseModel):
    """User creation request model."""
    email: str
    password: str
    first_name: str
    last_name: str


@router.post("/users/", response_model=User, status_code=201)
async def create_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Create a new user account.
    
    Args:
        user_data: User creation data
        auth_service: Authentication service
        
    Returns:
        Created user object
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        user = await auth_service.register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### User Documentation

Write clear, actionable documentation:

```markdown
# User Authentication

## Overview
This guide explains how to authenticate users in Cognie.

## Prerequisites
- Valid email address
- Password (minimum 8 characters)

## Steps

### 1. User Registration
1. Navigate to the registration page
2. Enter your email address
3. Create a secure password
4. Fill in your name
5. Click "Create Account"

### 2. Email Verification
1. Check your email for verification link
2. Click the verification link
3. Your account is now active

### 3. User Login
1. Go to the login page
2. Enter your email and password
3. Click "Sign In"
4. You're now logged in!

## Troubleshooting

**Can't log in?**
- Check your email and password
- Ensure your account is verified
- Try password reset if needed

**No verification email?**
- Check spam folder
- Request new verification email
- Contact support if issues persist
```

## Pull Request Process

### PR Checklist

Before submitting a PR, ensure:

- [ ] **Code follows style guidelines**
- [ ] **Tests pass and coverage is maintained**
- [ ] **Documentation is updated**
- [ ] **No breaking changes** (or clearly documented)
- [ ] **Security considerations** addressed
- [ ] **Performance impact** considered

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No console errors
- [ ] No linting errors

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline runs tests
   - Code coverage is checked
   - Linting and formatting verified

2. **Manual Review**
   - At least one approval required
   - Code quality review
   - Security review
   - Performance review

3. **Merge Process**
   - All checks pass
   - Required approvals received
   - Conflicts resolved
   - Squash and merge preferred

## Issue Reporting

### Issue Templates

#### Bug Report

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g. macOS, Windows, Linux]
- Browser: [e.g. Chrome, Firefox, Safari]
- Version: [e.g. 1.0.0]

## Screenshots
Add screenshots if applicable

## Additional Context
Any other context about the problem
```

#### Feature Request

```markdown
## Feature Description
Clear description of the feature

## Problem Statement
What problem does this solve?

## Proposed Solution
How should this work?

## Alternatives Considered
Other solutions you've considered

## Additional Context
Any other context or screenshots
```

### Issue Guidelines

- **Search existing issues** before creating new ones
- **Use descriptive titles** that summarize the issue
- **Provide detailed information** including steps to reproduce
- **Include relevant logs** and error messages
- **Add appropriate labels** to categorize issues

## Code of Conduct

### Our Standards

We are committed to providing a welcoming and inspiring community for all. We expect all contributors to:

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Be professional** in all interactions
- **Be helpful** to other contributors

### Unacceptable Behavior

The following behaviors are unacceptable:

- **Harassment** or discrimination
- **Trolling** or insulting comments
- **Personal attacks** or threats
- **Inappropriate language** or content

### Enforcement

Violations will be addressed by:

1. **Warning** for first-time violations
2. **Temporary ban** for repeated violations
3. **Permanent ban** for severe violations

### Reporting

Report violations to:
- **Email**: conduct@cognie.app
- **GitHub**: Create private issue

## Getting Help

### Resources

- **Documentation**: [docs.cognie.app](https://docs.cognie.app)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/cognie/discussions)
- **Issues**: [GitHub Issues](https://github.com/your-username/cognie/issues)
- **Wiki**: [GitHub Wiki](https://github.com/your-username/cognie/wiki)

### Community

- **Slack**: [Join our Slack](https://cognie.slack.com)
- **Discord**: [Join our Discord](https://discord.gg/cognie)
- **Email**: [support@cognie.app](mailto:support@cognie.app)

## Recognition

### Contributors

We recognize contributors through:

- **Contributor Hall of Fame** in README
- **GitHub Contributors** page
- **Release notes** acknowledgments
- **Special thanks** for significant contributions

### Contribution Levels

- **Bronze**: 1-5 contributions
- **Silver**: 6-20 contributions
- **Gold**: 21-50 contributions
- **Platinum**: 50+ contributions

## License

By contributing to Cognie, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Cognie! 🚀 
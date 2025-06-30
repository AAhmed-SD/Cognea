# Cognie - AI-Powered Productivity Platform

## Overview
Cognie is a comprehensive AI-powered productivity and scheduling web application designed to help users optimize their time, track goals, and enhance productivity through intelligent insights and automation.

## Features

### Core Features
- **Task Management**: Create, organize, and track tasks with AI-powered prioritization
- **Goal Tracking**: Set and monitor progress towards personal and professional goals
- **Smart Scheduling**: AI-optimized schedule blocks for maximum productivity
- **Habit Tracking**: Build and maintain positive habits with streak tracking
- **Flashcard Learning**: Spaced repetition learning system for knowledge retention
- **Analytics Dashboard**: Comprehensive productivity insights and trends
- **AI Integration**: OpenAI-powered task generation and schedule optimization

### Advanced Features
- **Real-time Notifications**: Instant updates on tasks, goals, and schedule changes
- **Calendar Integration**: Sync with external calendar systems
- **Notion Integration**: Seamless data synchronization with Notion
- **Privacy Controls**: Granular privacy settings and data export options
- **Performance Monitoring**: Real-time application performance tracking
- **Cost Tracking**: Monitor AI usage costs and token consumption

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.13**: Latest Python version for optimal performance
- **Supabase**: PostgreSQL database with real-time subscriptions
- **Redis**: Caching and session management
- **OpenAI GPT-4**: AI-powered task generation and optimization
- **Celery**: Background task processing
- **Prometheus**: Application monitoring and metrics

### Frontend
- **Next.js**: React framework for production
- **Tailwind CSS**: Utility-first CSS framework
- **Chart.js**: Data visualization and analytics
- **SWR**: Data fetching and caching

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Reverse proxy and load balancing
- **SSL/TLS**: Secure communication
- **Rate Limiting**: API protection
- **CORS**: Cross-origin resource sharing

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- Redis
- Supabase account

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/cognie.git
cd cognie
```

2. **Set up Python environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up Node.js environment**
```bash
npm install
```

4. **Configure environment variables**
```bash
cp env.production.template .env
# Edit .env with your configuration
```

5. **Set up database**
```bash
python setup_supabase_tables.py
```

6. **Start the development server**
```bash
# Backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
npm run dev
```

## Environment Variables

### Required Variables
```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_JWT_KEY=your_jwt_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Security
SECRET_KEY=your_secret_key

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Optional Variables
```bash
# Stripe Configuration (for payments)
STRIPE_PUBLISHING_KEY=your_stripe_publishing_key
STRIPE_API_KEY=your_stripe_api_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_PORT=9090

# Feature Flags
DISABLE_RATE_LIMIT=false
ENABLE_ANALYTICS=true
```

## API Documentation

Comprehensive API documentation is available at:
- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc`
- **API Reference**: See [API_ENDPOINTS.md](API_ENDPOINTS.md)

## Project Structure

```
cognie/
├── app/                    # Next.js frontend application
│   ├── components/         # React components
│   ├── models/            # Frontend data models
│   └── services/          # Frontend services
├── components/            # Shared React components
├── config/               # Configuration files
├── docs/                 # Documentation
├── middleware/           # FastAPI middleware
├── models/               # Database models
├── pages/                # Next.js pages
├── routes/               # API route handlers
├── services/             # Backend services
├── styles/               # CSS styles
├── tests/                # Test files
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
└── package.json         # Node.js dependencies
```

## Database Schema

### Core Tables
- **users**: User accounts and profiles
- **tasks**: Task management
- **goals**: Goal tracking
- **schedule_blocks**: Time scheduling
- **habits**: Habit tracking
- **flashcards**: Learning system
- **notifications**: User notifications
- **user_settings**: User preferences

### Analytics Tables
- **productivity_scores**: Productivity metrics
- **focus_sessions**: Focus time tracking
- **task_completions**: Task completion data
- **habit_logs**: Habit completion logs

## Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_async_comprehensive.py

# Run with coverage
pytest --cov=.

# Run integration tests
pytest tests/ -m integration
```

### Frontend Tests
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## Deployment

### Production Deployment
```bash
# Run deployment script
./deploy_production.sh
```

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up -d
```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt password encryption
- **Rate Limiting**: API protection against abuse
- **CORS Protection**: Cross-origin request security
- **Input Validation**: Comprehensive request validation
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Content Security Policy headers
- **HTTPS Enforcement**: Secure communication

## Performance Features

- **Redis Caching**: Fast data access
- **Database Indexing**: Optimized queries
- **Connection Pooling**: Efficient database connections
- **Background Tasks**: Asynchronous processing
- **CDN Integration**: Static asset delivery
- **Compression**: Response compression
- **Monitoring**: Real-time performance tracking

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend components
- Write comprehensive tests
- Update documentation for new features
- Follow conventional commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/cognie/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/cognie/discussions)
- **Email**: support@cognie.com

## Roadmap

### Phase 1 (Current)
- ✅ Core task management
- ✅ Goal tracking
- ✅ Basic AI integration
- ✅ User authentication
- ✅ Analytics dashboard

### Phase 2 (Next)
- 🔄 Advanced AI features
- 🔄 Mobile app development
- 🔄 Team collaboration
- 🔄 Advanced analytics
- 🔄 Third-party integrations

### Phase 3 (Future)
- 📋 Enterprise features
- 📋 Advanced reporting
- 📋 AI-powered insights
- 📋 Custom workflows
- 📋 API marketplace

## Acknowledgments

- OpenAI for AI capabilities
- Supabase for database infrastructure
- FastAPI community for the excellent framework
- Next.js team for the React framework
- All contributors and supporters

---

**Built with ❤️ for productivity enthusiasts**

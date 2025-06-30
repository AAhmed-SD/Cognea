# Cognie - AI-Powered Productivity & Learning Platform

## 🚀 **Status: Production Ready**

Cognie is a comprehensive AI-powered productivity and learning platform that combines intelligent task management, habit tracking, and automated flashcard generation from your Notion content.

## ✨ **Key Features**

### 🤖 **AI-Powered Intelligence**
- **Smart Task Generation** - AI creates personalized tasks based on your goals and schedule
- **Intelligent Scheduling** - Optimizes your day using AI-driven time management
- **Automated Insights** - Real-time productivity analytics and recommendations
- **Conversational AI** - Natural language interaction for task management

### 📚 **Notion Integration (FULLY IMPLEMENTED)**
- **Real-time Webhooks** - Automatic sync when Notion pages/databases change
- **AI Flashcard Generation** - Converts Notion content into study materials
- **Bidirectional Sync** - Keep Cognie and Notion in perfect harmony
- **Multi-user Support** - Each user's content stays private and organized
- **Rate-limited Processing** - Handles high-volume updates efficiently
- **Security Verification** - HMAC-SHA256 webhook signatures for security

### 📊 **Productivity Analytics**
- **Real-time Dashboard** - Visual insights into your productivity patterns
- **Goal Tracking** - Monitor progress toward your objectives
- **Habit Formation** - Build and maintain positive routines
- **Performance Metrics** - Detailed analytics on focus time and task completion

### 🔐 **Enterprise Security**
- **JWT Authentication** - Secure user sessions with refresh tokens
- **Rate Limiting** - Protection against abuse and overload
- **CORS Protection** - Secure cross-origin resource sharing
- **Input Validation** - Comprehensive data sanitization
- **Audit Logging** - Complete activity tracking for compliance

## 🏗️ **Architecture**

### **Backend Stack**
- **FastAPI** - High-performance async web framework
- **Supabase** - PostgreSQL database with real-time subscriptions
- **OpenAI GPT-4** - Advanced AI for task generation and insights
- **Redis** - Caching and rate limiting
- **Celery** - Background task processing

### **Frontend Stack**
- **Next.js** - React framework with SSR
- **Tailwind CSS** - Utility-first styling
- **Chart.js** - Interactive data visualizations
- **Supabase Auth** - Secure authentication

### **Infrastructure**
- **Docker** - Containerized deployment
- **Nginx** - Reverse proxy and load balancing
- **Prometheus** - Metrics collection and monitoring
- **Grafana** - Visualization and alerting

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- Redis server
- Supabase account
- OpenAI API key

### **Quick Start**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd personal-agent
   ```

2. **Set up environment variables**
   ```bash
   cp env.production.template .env
   # Edit .env with your actual values
   ```

3. **Install dependencies**
   ```bash
   # Backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Frontend
   npm install
   ```

4. **Set up database**
   ```bash
   python setup_supabase_tables.py
   ```

5. **Run the application**
   ```bash
   # Backend (in one terminal)
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

   # Frontend (in another terminal)
   npm run dev
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/health

## 🔗 **Notion Integration Setup**

### **Complete Webhook Implementation**

The Notion integration is fully implemented with production-ready webhooks:

1. **Create Notion Integration**
   - Go to [Notion Integrations](https://www.notion.so/my-integrations)
   - Create new integration with read/write permissions

2. **Configure Webhooks**
   - Set up webhook endpoints in Notion dashboard
   - Configure signature verification
   - Test webhook delivery

3. **Connect Your Account**
   - Use the "Connect Notion" button in Cognie
   - Authorize access to your workspace
   - Start syncing content automatically

4. **Automatic Processing**
   - Content changes trigger webhooks instantly
   - AI generates flashcards automatically
   - Sync status tracked in real-time

See [Notion Webhook Setup Guide](docs/NOTION_WEBHOOK_SETUP.md) for detailed instructions.

## 📊 **API Endpoints**

### **Core Endpoints**
- `GET /api/` - API information
- `GET /api/health` - Health check
- `GET /api/metrics` - Prometheus metrics

### **Authentication**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/logout` - User logout

### **Tasks & Goals**
- `GET /api/tasks` - List user tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### **Notion Integration**
- `POST /api/notion/auth` - Authenticate with Notion
- `GET /api/notion/pages` - List Notion pages
- `POST /api/notion/generate-flashcards` - Generate flashcards
- `POST /api/notion/sync` - Sync content
- `POST /api/notion/webhook/notion` - Webhook receiver
- `GET /api/notion/webhook/notion/verify` - Webhook verification

### **Analytics**
- `GET /api/analytics/productivity` - Productivity metrics
- `GET /api/analytics/goals` - Goal progress
- `GET /api/analytics/habits` - Habit tracking

See [API Documentation](docs/API_ENDPOINTS.md) for complete endpoint details.

## 🧪 **Testing**

### **Run All Tests**
```bash
python -m pytest tests/ -v
```

### **Test Categories**
- **Unit Tests** - Individual component testing
- **Integration Tests** - API endpoint testing
- **Notion Webhook Tests** - Webhook processing validation
- **Authentication Tests** - Security verification

### **Test Coverage**
- ✅ Backend API endpoints
- ✅ Database operations
- ✅ Authentication flows
- ✅ Notion webhook processing
- ✅ AI service integration
- ✅ Rate limiting
- ✅ Error handling

## 🚀 **Deployment**

### **Production Deployment**
```bash
# Run deployment script
./deploy_production.sh
```

### **Environment Configuration**
- Copy `env.production.template` to `.env.production`
- Configure all required environment variables
- Set up SSL certificates
- Configure domain and DNS

### **Monitoring**
- Prometheus metrics at `/metrics`
- Health checks at `/health`
- Application logs in `/var/log/personal-agent/`
- Error tracking and alerting

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

## 📈 **Performance**

### **Optimizations**
- **Redis Caching** - Fast response times for frequently accessed data
- **Database Indexing** - Optimized queries for large datasets
- **Rate Limiting** - Protection against abuse
- **Background Processing** - Non-blocking operations
- **CDN Integration** - Fast static asset delivery

### **Scalability**
- **Horizontal Scaling** - Multiple application instances
- **Load Balancing** - Distributed traffic across servers
- **Database Sharding** - Partitioned data storage
- **Microservices Ready** - Modular architecture

## 🔒 **Security**

### **Authentication & Authorization**
- JWT tokens with refresh mechanism
- Role-based access control
- Session management
- Password hashing with bcrypt

### **Data Protection**
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

### **Infrastructure Security**
- HTTPS enforcement
- Security headers
- Rate limiting
- Audit logging

## 🤝 **Contributing**

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### **Code Standards**
- Follow PEP 8 for Python code
- Use TypeScript for frontend
- Write comprehensive tests
- Document new features

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

### **Documentation**
- [API Documentation](docs/API_ENDPOINTS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Notion Integration Guide](docs/NOTION_WEBHOOK_SETUP.md)
- [Security Guide](docs/SECURITY_PERFORMANCE.md)

### **Issues**
- Report bugs via GitHub Issues
- Request features through feature requests
- Ask questions in discussions

## 🎯 **Roadmap**

### **Completed Features**
- ✅ Core API infrastructure
- ✅ User authentication
- ✅ Task management
- ✅ Goal tracking
- ✅ Notion integration with webhooks
- ✅ AI-powered insights
- ✅ Analytics dashboard
- ✅ Production deployment

### **Upcoming Features**
- 🔄 Calendar integration (Google, Outlook)
- 🔄 Advanced AI features
- 🔄 Mobile application
- 🔄 Team collaboration
- 🔄 Advanced analytics
- 🔄 Third-party integrations

---

**Built with ❤️ for productivity and learning**

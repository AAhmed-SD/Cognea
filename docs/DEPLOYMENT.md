# Deployment Guide

## Overview
This guide covers deploying Cognie to production environments with best practices for security, performance, and scalability.

## Prerequisites

### System Requirements
- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB+ (8GB+ recommended)
- **Storage**: 20GB+ SSD
- **OS**: Ubuntu 20.04+ / CentOS 8+ / macOS 12+

### Software Requirements
- Python 3.13+
- Node.js 18+
- Redis 6+
- Nginx
- Docker (optional)
- SSL certificate

## Environment Setup

### 1. Production Environment Variables

Create a production `.env` file:

```bash
# Copy template
cp env.production.template .env.production

# Edit with production values
nano .env.production
```

**Required Variables:**
```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_JWT_KEY=your_jwt_key

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your_openai_key

# Security
SECRET_KEY=your_very_long_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cognie

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=noreply@yourdomain.com

# Monitoring
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_PORT=9090

# Feature Flags
DISABLE_RATE_LIMIT=false
ENABLE_ANALYTICS=true
ENABLE_MONITORING=true

# Stripe (if using payments)
STRIPE_PUBLISHING_KEY=pk_live_your_key
STRIPE_API_KEY=sk_live_your_key
```

### 2. Database Setup

#### Supabase Production Setup
1. Create a new Supabase project
2. Run the setup script:
```bash
python setup_supabase_tables.py
```

#### Local PostgreSQL (Alternative)
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb cognie
sudo -u postgres createuser cognie_user
sudo -u postgres psql -c "ALTER USER cognie_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cognie TO cognie_user;"
```

### 3. Redis Setup

```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf

# Set password
requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

## Deployment Methods

### Method 1: Direct Deployment

#### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.13 python3.13-venv python3.13-dev
sudo apt install nodejs npm
sudo apt install nginx
sudo apt install redis-server
sudo apt install postgresql postgresql-contrib

# Install PM2 for process management
npm install -g pm2
```

#### 2. Application Setup
```bash
# Clone repository
git clone https://github.com/your-username/cognie.git
cd cognie

# Set up Python environment
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up Node.js environment
npm install
npm run build

# Set environment
cp .env.production .env
```

#### 3. Nginx Configuration
```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/cognie

# Add configuration
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    }
    
    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /path/to/cognie/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/cognie /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 5. PM2 Configuration
```bash
# Create PM2 ecosystem file
nano ecosystem.config.js

# Add configuration
module.exports = {
  apps: [
    {
      name: 'cognie-backend',
      script: 'main.py',
      interpreter: './venv/bin/python',
      instances: 'max',
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 8000
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_file: './logs/backend-combined.log',
      time: true
    },
    {
      name: 'cognie-frontend',
      script: 'npm',
      args: 'start',
      cwd: './',
      instances: 1,
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend-combined.log',
      time: true
    }
  ]
};

# Start applications
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Method 2: Docker Deployment

#### 1. Dockerfile
```dockerfile
# Backend Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/cognie
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: cognie
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass your_redis_password
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
```

#### 3. Deploy with Docker
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale backend
docker-compose up -d --scale backend=3
```

### Method 3: Cloud Deployment

#### AWS Deployment
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS
aws configure

# Deploy to EC2
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx
```

#### Google Cloud Deployment
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Deploy to App Engine
gcloud app deploy app.yaml
```

## Monitoring and Logging

### 1. Application Monitoring
```bash
# Install monitoring tools
pip install prometheus-client
npm install -g pm2

# Set up Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvf prometheus-*.tar.gz
cd prometheus-*

# Configure Prometheus
nano prometheus.yml
```

### 2. Log Management
```bash
# Create log directory
mkdir -p logs

# Configure log rotation
sudo nano /etc/logrotate.d/cognie

# Add configuration
/path/to/cognie/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### 3. Health Checks
```bash
# Create health check script
nano health_check.sh

#!/bin/bash
# Check backend
curl -f http://localhost:8000/api/health || exit 1

# Check frontend
curl -f http://localhost:3000 || exit 1

# Check database
pg_isready -h localhost -p 5432 || exit 1

# Check Redis
redis-cli ping || exit 1
```

## Security Hardening

### 1. Firewall Configuration
```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. System Hardening
```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Install security updates
sudo unattended-upgrades --enable

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Application Security
```bash
# Set secure file permissions
chmod 600 .env.production
chmod 700 logs/

# Configure app security
# - Rate limiting enabled
# - CORS properly configured
# - Input validation
# - SQL injection protection
```

## Backup Strategy

### 1. Database Backup
```bash
# Create backup script
nano backup_db.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump cognie > $BACKUP_DIR/cognie_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/cognie_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### 2. File Backup
```bash
# Backup application files
rsync -avz /path/to/cognie/ /backups/app/
```

### 3. Automated Backups
```bash
# Add to crontab
crontab -e

# Daily database backup at 2 AM
0 2 * * * /path/to/backup_db.sh

# Weekly file backup on Sunday at 3 AM
0 3 * * 0 rsync -avz /path/to/cognie/ /backups/app/
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- Analyze tables
ANALYZE tasks;
ANALYZE goals;
ANALYZE schedule_blocks;
```

### 2. Caching Strategy
```python
# Redis caching configuration
CACHE_TTL = 3600  # 1 hour
CACHE_PREFIX = "cognie:"

# Cache frequently accessed data
- User profiles
- Task lists
- Analytics data
- API responses
```

### 3. CDN Configuration
```bash
# Configure CloudFlare or similar CDN
# - Enable caching for static assets
# - Configure edge locations
# - Enable compression
# - Set security headers
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check logs
pm2 logs
tail -f logs/backend-error.log

# Check environment
echo $NODE_ENV
python -c "import os; print(os.getenv('DATABASE_URL'))"
```

#### 2. Database Connection Issues
```bash
# Test database connection
psql -h localhost -U user -d cognie -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql
```

#### 3. Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping

# Check Redis status
sudo systemctl status redis
```

#### 4. Nginx Issues
```bash
# Check Nginx configuration
sudo nginx -t

# Check Nginx status
sudo systemctl status nginx

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### Performance Monitoring
```bash
# Monitor system resources
htop
iotop
nethogs

# Monitor application performance
pm2 monit
```

## Maintenance

### Regular Maintenance Tasks
```bash
# Weekly
- Update system packages
- Check disk space
- Review logs
- Test backups

# Monthly
- Security updates
- Performance review
- Database maintenance
- SSL certificate renewal

# Quarterly
- Full system audit
- Performance optimization
- Security assessment
- Backup restoration test
```

## Support and Documentation

### Useful Commands
```bash
# Restart services
pm2 restart all
sudo systemctl restart nginx
sudo systemctl restart redis
sudo systemctl restart postgresql

# View real-time logs
pm2 logs --lines 100
tail -f logs/backend-combined.log

# Monitor resources
pm2 monit
htop
```

### Emergency Procedures
```bash
# Emergency restart
pm2 restart all
sudo systemctl restart nginx

# Rollback deployment
git checkout HEAD~1
pm2 restart all

# Emergency maintenance mode
echo "Maintenance mode" > maintenance.html
```

---

For additional support, refer to:
- [API Documentation](API_ENDPOINTS.md)
- [Security Guide](SECURITY_PERFORMANCE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md) 
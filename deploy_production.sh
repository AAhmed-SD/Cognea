#!/bin/bash

# Production Deployment Script for Personal Agent API
# This script sets up and deploys the application to production

set -e  # Exit on any error

echo "🚀 Starting production deployment..."

# Configuration
APP_NAME="personal-agent-api"
DEPLOY_DIR="/opt/personal-agent"
SERVICE_NAME="personal-agent"
DOMAIN="api.yourdomain.com"
SSL_EMAIL="admin@yourdomain.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    local missing_deps=()
    
    for cmd in python3 pip3 git nginx certbot redis-cli; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Please install missing dependencies and try again"
        exit 1
    fi
    
    print_status "All dependencies found"
}

# Create deployment directory
setup_directories() {
    print_status "Setting up deployment directories..."
    
    sudo mkdir -p $DEPLOY_DIR
    sudo mkdir -p /var/log/$SERVICE_NAME
    sudo mkdir -p /etc/systemd/system
    sudo mkdir -p /etc/nginx/sites-available
    sudo mkdir -p /etc/nginx/sites-enabled
    
    # Set ownership
    sudo chown -R $USER:$USER $DEPLOY_DIR
    sudo chown -R $USER:$USER /var/log/$SERVICE_NAME
    
    print_status "Directories created"
}

# Clone or update code
deploy_code() {
    print_status "Deploying application code..."
    
    if [ ! -d "$DEPLOY_DIR/.git" ]; then
        # First time deployment
        git clone https://github.com/yourusername/personal-agent.git $DEPLOY_DIR
    else
        # Update existing deployment
        cd $DEPLOY_DIR
        git pull origin main
    fi
    
    cd $DEPLOY_DIR
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_status "Code deployed successfully"
}

# Setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."
    
    if [ ! -f "$DEPLOY_DIR/.env.production" ]; then
        print_warning "Production environment file not found"
        print_status "Please create .env.production from env.production.template"
        print_status "and fill in your actual values"
        exit 1
    fi
    
    # Set proper permissions
    chmod 600 $DEPLOY_DIR/.env.production
    
    print_status "Environment configured"
}

# Setup systemd service
setup_systemd() {
    print_status "Setting up systemd service..."
    
    cat << EOF | sudo tee /etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=Personal Agent API
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$DEPLOY_DIR
Environment=PATH=$DEPLOY_DIR/venv/bin
ExecStart=$DEPLOY_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    print_status "Systemd service configured"
}

# Setup Nginx
setup_nginx() {
    print_status "Setting up Nginx..."
    
    cat << EOF | sudo tee /etc/nginx/sites-available/$DOMAIN
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy to FastAPI application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000;
    }
    
    # Metrics endpoint (protected)
    location /metrics {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF
    
    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    
    # Test Nginx configuration
    sudo nginx -t
    
    print_status "Nginx configured"
}

# Setup SSL certificate
setup_ssl() {
    print_status "Setting up SSL certificate..."
    
    # Stop Nginx temporarily
    sudo systemctl stop nginx
    
    # Obtain SSL certificate
    sudo certbot certonly --standalone -d $DOMAIN --email $SSL_EMAIL --agree-tos --non-interactive
    
    # Start Nginx
    sudo systemctl start nginx
    
    # Setup automatic renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    print_status "SSL certificate configured"
}

# Setup Redis
setup_redis() {
    print_status "Setting up Redis..."
    
    # Install Redis if not already installed
    if ! command -v redis-server &> /dev/null; then
        print_status "Installing Redis..."
        sudo apt-get update
        sudo apt-get install -y redis-server
    fi
    
    # Configure Redis for production
    sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
    
    # Update Redis configuration
    sudo sed -i 's/bind 127.0.0.1/bind 127.0.0.1/' /etc/redis/redis.conf
    sudo sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
    sudo sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    
    sudo systemctl enable redis-server
    sudo systemctl restart redis-server
    
    print_status "Redis configured"
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Install Prometheus Node Exporter
    if ! command -v node_exporter &> /dev/null; then
        print_status "Installing Prometheus Node Exporter..."
        wget https://github.com/prometheus/node_exporter/releases/download/v1.3.1/node_exporter-1.3.1.linux-amd64.tar.gz
        tar xvf node_exporter-1.3.1.linux-amd64.tar.gz
        sudo cp node_exporter-1.3.1.linux-amd64/node_exporter /usr/local/bin/
        rm -rf node_exporter-1.3.1.linux-amd64*
        
        # Create systemd service for node_exporter
        cat << EOF | sudo tee /etc/systemd/system/node_exporter.service
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        
        sudo useradd -rs /bin/false prometheus
        sudo systemctl daemon-reload
        sudo systemctl enable node_exporter
        sudo systemctl start node_exporter
    fi
    
    print_status "Monitoring configured"
}

# Setup firewall
setup_firewall() {
    print_status "Setting up firewall..."
    
    # Allow SSH, HTTP, HTTPS
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Enable firewall
    sudo ufw --force enable
    
    print_status "Firewall configured"
}

# Start services
start_services() {
    print_status "Starting services..."
    
    sudo systemctl start redis-server
    sudo systemctl start $SERVICE_NAME
    sudo systemctl start nginx
    
    # Wait for services to start
    sleep 5
    
    # Check service status
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_status "Personal Agent API is running"
    else
        print_error "Personal Agent API failed to start"
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi
    
    if sudo systemctl is-active --quiet nginx; then
        print_status "Nginx is running"
    else
        print_error "Nginx failed to start"
        sudo systemctl status nginx
        exit 1
    fi
    
    print_status "All services started successfully"
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    cd $DEPLOY_DIR
    source venv/bin/activate
    
    # Run basic health check
    sleep 10  # Wait for service to be ready
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "Health check passed"
    else
        print_error "Health check failed"
        exit 1
    fi
    
    print_status "Tests completed"
}

# Main deployment function
main() {
    print_status "Starting production deployment for $DOMAIN"
    
    check_dependencies
    setup_directories
    deploy_code
    setup_environment
    setup_redis
    setup_systemd
    setup_nginx
    setup_ssl
    setup_monitoring
    setup_firewall
    start_services
    run_tests
    
    print_status "🎉 Deployment completed successfully!"
    print_status "Your API is now available at: https://$DOMAIN"
    print_status "Health check: https://$DOMAIN/health"
    print_status "API docs: https://$DOMAIN/api/docs"
    
    print_warning "Don't forget to:"
    print_warning "1. Update your DNS records to point $DOMAIN to this server"
    print_warning "2. Configure your monitoring and alerting"
    print_warning "3. Set up regular backups"
    print_warning "4. Monitor logs: sudo journalctl -u $SERVICE_NAME -f"
}

# Run main function
main "$@" 
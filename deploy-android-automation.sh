#!/bin/bash

# Linux Cloud Server Deployment Script for Android App Automation
# This script sets up the complete environment for Android automation

set -e  # Exit on any error

echo "🚀 Starting Linux Cloud Server Deployment for Android App Automation"
echo "=================================================================="

# Configuration
PROJECT_DIR="/opt/flight-scraper"
DOCKER_COMPOSE_FILE="docker-compose.yml"
NGINX_CONFIG="nginx.conf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root. Consider using a non-root user with sudo privileges."
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    sudo apt-get update -y
    sudo apt-get upgrade -y
    log "System packages updated successfully"
}

# Install Docker
install_docker() {
    log "Installing Docker..."
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        info "Docker is already installed"
        docker --version
        return
    fi
    
    # Install Docker dependencies
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log "Docker installed successfully"
    docker --version
}

# Install Docker Compose
install_docker_compose() {
    log "Installing Docker Compose..."
    
    # Check if Docker Compose is already installed
    if command -v docker-compose &> /dev/null; then
        info "Docker Compose is already installed"
        docker-compose --version
        return
    fi
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log "Docker Compose installed successfully"
    docker-compose --version
}

# Install additional dependencies
install_dependencies() {
    log "Installing additional dependencies..."
    
    sudo apt-get install -y \
        git \
        wget \
        curl \
        unzip \
        python3 \
        python3-pip \
        nginx \
        ufw \
        htop \
        tree
    
    log "Additional dependencies installed successfully"
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Enable UFW
    sudo ufw --force enable
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow application ports
    sudo ufw allow 3000/tcp  # Frontend
    sudo ufw allow 8000/tcp  # Backend API
    sudo ufw allow 5555/tcp  # Android ADB
    sudo ufw allow 6080/tcp  # Android VNC
    
    log "Firewall configured successfully"
}

# Setup project directory
setup_project() {
    log "Setting up project directory..."
    
    # Create project directory
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    
    # Clone or copy project files
    if [ -d ".git" ]; then
        info "Copying project files to $PROJECT_DIR"
        cp -r . $PROJECT_DIR/
    else
        error "Not in a git repository. Please ensure you're in the project directory."
    fi
    
    cd $PROJECT_DIR
    
    log "Project directory setup completed"
}

# Configure environment
configure_environment() {
    log "Configuring environment..."
    
    # Create environment file
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/flight_scraper
POSTGRES_DB=flight_scraper
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Configuration
REDIS_URL=redis://redis:6379

# Application Configuration
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)

# Android Automation Configuration
ANDROID_SCREENSHOTS_DIR=/app/screenshots
ANDROID_DOWNLOADS_DIR=/app/downloads
ANDROID_CONTAINER_IMAGE=budtmo/docker-android:api_30_x86
ANDROID_CONTAINER_CPU_LIMIT=2.0
ANDROID_CONTAINER_MEMORY_LIMIT=4g

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:80

# Frontend Configuration
VITE_API_URL=http://localhost:8000/api/v1
EOF
    
    log "Environment configuration completed"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Wait for database to be ready
    sleep 10
    
    # Run platform migration
    docker-compose -f $DOCKER_COMPOSE_FILE exec backend python migrate_add_platform_fields.py
    
    # Run Android automation migration
    docker-compose -f $DOCKER_COMPOSE_FILE exec backend python migrate_android_automation.py
    
    # Add initial 12306 platform
    docker-compose -f $DOCKER_COMPOSE_FILE exec backend python add_12306_platform.py
    
    log "Database migrations completed successfully"
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    # Build and start services
    docker-compose -f $DOCKER_COMPOSE_FILE down --remove-orphans
    docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log "Application deployed successfully"
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    # Check database
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T db pg_isready -U postgres; then
        log "✅ Database is healthy"
    else
        error "❌ Database is not healthy"
    fi
    
    # Check Redis
    if docker-compose -f $DOCKER_COMPOSE_FILE exec -T redis redis-cli ping | grep -q PONG; then
        log "✅ Redis is healthy"
    else
        error "❌ Redis is not healthy"
    fi
    
    # Check backend API
    if curl -f http://localhost:8000/api/v1/android-automation/health > /dev/null 2>&1; then
        log "✅ Backend API is healthy"
    else
        warning "⚠️ Backend API health check failed (may still be starting)"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log "✅ Frontend is healthy"
    else
        warning "⚠️ Frontend health check failed (may still be starting)"
    fi
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring script
    cat > monitor.sh << 'EOF'
#!/bin/bash

# Simple monitoring script
echo "=== Flight Scraper Android Automation Status ==="
echo "Date: $(date)"
echo ""

# Docker containers status
echo "Docker Containers:"
docker-compose -f docker-compose-android.yml ps

echo ""
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""
echo "Disk Usage:"
df -h

echo ""
echo "Memory Usage:"
free -h
EOF
    
    chmod +x monitor.sh
    
    # Create systemd service for monitoring
    sudo tee /etc/systemd/system/flight-scraper-monitor.service > /dev/null << EOF
[Unit]
Description=Flight Scraper Monitoring
After=network.target

[Service]
Type=oneshot
ExecStart=$PROJECT_DIR/monitor.sh
User=$USER
WorkingDirectory=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    log "Monitoring setup completed"
}

# Create management scripts
create_management_scripts() {
    log "Creating management scripts..."
    
    # Start script
    cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/flight-scraper
docker-compose -f docker-compose-android.yml up -d
echo "Flight Scraper Android Automation started"
EOF
    
    # Stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
cd /opt/flight-scraper
docker-compose -f docker-compose-android.yml down
echo "Flight Scraper Android Automation stopped"
EOF
    
    # Restart script
    cat > restart.sh << 'EOF'
#!/bin/bash
cd /opt/flight-scraper
docker-compose -f docker-compose-android.yml restart
echo "Flight Scraper Android Automation restarted"
EOF
    
    # Logs script
    cat > logs.sh << 'EOF'
#!/bin/bash
cd /opt/flight-scraper
docker-compose -f docker-compose-android.yml logs -f
EOF
    
    # Make scripts executable
    chmod +x start.sh stop.sh restart.sh logs.sh monitor.sh
    
    log "Management scripts created successfully"
}

# Test Android automation
test_android_automation() {
    log "Testing Android automation..."
    
    # Wait for services to be fully ready
    sleep 60
    
    # Test API health
    if curl -f http://localhost:8000/api/v1/android-automation/health; then
        log "✅ Android automation API is responding"
    else
        warning "⚠️ Android automation API test failed"
    fi
    
    # Test platform list
    if curl -f http://localhost:8000/api/v1/platforms/; then
        log "✅ Platform API is responding"
    else
        warning "⚠️ Platform API test failed"
    fi
    
    log "Android automation testing completed"
}

# Main deployment function
main() {
    log "Starting deployment process..."
    
    check_root
    update_system
    install_docker
    install_docker_compose
    install_dependencies
    configure_firewall
    setup_project
    configure_environment
    deploy_application
    run_migrations
    setup_monitoring
    create_management_scripts
    test_android_automation
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "=================================="
    echo ""
    echo "Access URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo "  Android VNC: http://localhost:6080"
    echo ""
    echo "Management Commands:"
    echo "  Start: ./start.sh"
    echo "  Stop: ./stop.sh"
    echo "  Restart: ./restart.sh"
    echo "  Logs: ./logs.sh"
    echo "  Monitor: ./monitor.sh"
    echo ""
    echo "Next Steps:"
    echo "  1. Access the frontend at http://localhost:3000"
    echo "  2. Login with admin/admin123"
    echo "  3. Navigate to Settings > Target Platform Settings"
    echo "  4. Test Android automation with the 12306 platform"
    echo ""
    echo "For Android automation testing:"
    echo "  POST http://localhost:8000/api/v1/android-automation/start"
    echo "  Body: {\"platform_id\": 1, \"capture_screenshot\": true}"
    echo ""
}

# Run main function
main "$@"

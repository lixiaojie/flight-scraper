# Flight Data Scraping Tool - Complete Setup Guide

## 🚀 Project Overview

This is a comprehensive flight data scraping tool that allows users to:
- Create and manage scraping tasks for multiple flight booking platforms
- Automate web and mobile app interactions to extract flight data
- Compare prices across different sources
- Monitor task execution and results through a modern web interface

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: Database ORM for data persistence
- **Celery**: Distributed task queue for background processing
- **Selenium/Playwright**: Web automation for browser interactions (planned)
- **Appium**: Mobile app automation for iOS/Android (planned)
- **Tesseract**: OCR for extracting text from screenshots (planned)
- **PostgreSQL**: Primary database for data storage
- **Redis**: Message broker for Celery

### Frontend (React/TypeScript)
- **React 18**: Modern UI framework with TypeScript
- **Vite**: Fast build tool and development server
- **TailwindCSS**: Utility-first CSS framework
- **ShadCN/UI**: Modern component library
- **React Query**: Data fetching and caching
- **Framer Motion**: Smooth animations
- **React Router**: Client-side routing

## 📋 Prerequisites

### Required Software
- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git** (for cloning the repository)

### Optional (for local development)
- **Node.js** 18+ (for frontend development)
- **Python** 3.11+ (for backend development)

### System Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: At least 2GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)

## 🐳 Quick Start (Docker - Recommended)

### Step 1: Clone the Repository
```bash
# Clone the repository
git clone <repository-url>
cd flight-scraper
```

### Step 2: Start All Services
```bash
# Start all services in detached mode
docker-compose up -d

# Wait for services to be ready (this may take 2-3 minutes on first run)
docker-compose ps
```

### Step 3: Verify Installation
```bash
# Run the deployment test script
chmod +x test_deployment.sh
./test_deployment.sh
```

### Step 4: Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Step 5: Create Demo User
```bash
# Create a demo user for testing
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
try:
    # Check if admin user already exists
    existing_user = db.query(User).filter(User.username == 'admin').first()
    if existing_user:
        print('Demo user already exists: admin/admin123')
    else:
        user = User(
            username='admin',
            email='admin@example.com',
            hashed_password=get_password_hash('admin123')
        )
        db.add(user)
        db.commit()
        print('Demo user created: admin/admin123')
finally:
    db.close()
"
```

### Step 6: Login and Explore
1. Open http://localhost:3000 in your browser
2. Login with credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Explore the dashboard and create your first task!

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Stop conflicting services or change ports in docker-compose.yml
```

#### 2. Docker Build Fails
```bash
# Clean up Docker cache and rebuild
docker-compose down --volumes --remove-orphans
docker system prune -f
docker-compose up --build -d
```

#### 3. Database Connection Issues
```bash
# Check database health
docker-compose exec db pg_isready -U postgres

# Reset database (WARNING: This will delete all data)
docker-compose down --volumes
docker-compose up -d
```

#### 4. Frontend Not Loading
```bash
# Check frontend logs
docker-compose logs frontend

# Restart frontend service
docker-compose restart frontend
```

#### 5. Backend API Errors
```bash
# Check backend logs
docker-compose logs backend

# Check if all dependencies are installed
docker-compose exec backend pip list
```

### Getting Help
If you encounter issues:
1. Check the logs: `docker-compose logs [service-name]`
2. Run the test script: `./test_deployment.sh`
3. Verify all services are running: `docker-compose ps`
4. Check the API documentation: http://localhost:8000/docs

## 💻 Local Development Setup

If you prefer to run the application locally without Docker:

### Prerequisites for Local Development
- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **PostgreSQL 15+** (running locally or in Docker)
- **Redis 7+** (running locally or in Docker)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy example environment file
   cp env.example .env
   
   # Edit .env with your configuration
   # Key variables to set:
   # DATABASE_URL=postgresql://postgres:password@localhost:5432/flight_scraper
   # REDIS_URL=redis://localhost:6379/0
   # SECRET_KEY=your-secret-key-here
   ```

5. **Set up database:**
   ```bash
   # Create database (if not exists)
   createdb flight_scraper
   
   # Run database migrations
   alembic upgrade head
   ```

6. **Start the backend:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   # Copy example environment file
   cp env.example .env
   
   # Edit .env with your configuration
   # VITE_API_URL=http://localhost:8000/api/v1
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

### Celery Worker (Optional)

For background task processing:

1. **Start Redis** (if not using Docker):
   ```bash
   redis-server
   ```

2. **Start Celery worker:**
   ```bash
   cd backend
   celery -A app.core.celery worker --loglevel=info
   ```

## 🛠️ Development Commands

### Docker Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs [service-name]

# Restart a service
docker-compose restart [service-name]

# Rebuild and start
docker-compose up --build -d

# Clean up everything
docker-compose down --volumes --remove-orphans
```

### Backend Commands
```bash
# Run tests
pytest

# Format code
black .
isort .

# Lint code
flake8

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend Commands
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 📁 Project Structure

```
flight-scraper/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Celery tasks
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── lib/            # Utilities
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile         # Frontend container
├── docker-compose.yml      # Docker services
├── test_deployment.sh      # Deployment test script
└── README.md              # Project documentation
```

## ⚙️ Environment Configuration

### Backend Environment Variables
Create a `.env` file in the `backend/` directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/flight_scraper

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production

# API Settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Scraping Settings
DEFAULT_QUERY_INTERVAL_MIN=5
DEFAULT_QUERY_INTERVAL_MAX=15
MAX_RETRIES=3
REQUEST_TIMEOUT=30

# File Storage
UPLOAD_DIR=uploads
SCREENSHOTS_DIR=screenshots
LOGS_DIR=logs
```

### Frontend Environment Variables
Create a `.env` file in the `frontend/` directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000/api/v1

# Development Settings
VITE_DEV_MODE=true
```

## 🎯 Features Status

### ✅ Completed Features

1. **Project Structure & Architecture**
   - Complete backend API with FastAPI
   - Modern React frontend with TypeScript
   - Docker containerization with health checks
   - Database models and relationships

2. **Authentication System**
   - User registration and login
   - JWT token-based authentication
   - Protected routes and middleware
   - Demo user creation

3. **Dashboard & Navigation**
   - Modern header navigation (Home, Task Management, System Config)
   - Task overview dashboard with statistics
   - Real-time updates and monitoring
   - Dark/light theme support

4. **Task Management**
   - Create, read, update, delete tasks
   - Task status tracking (pending, running, completed, failed)
   - Task scheduling and frequency options
   - Modern table layout with actions

5. **System Configuration**
   - Platform configuration (web/mobile)
   - Account management interface
   - Query rules and intervals
   - Platform-specific settings

6. **Modern UI/UX**
   - Responsive design for all screen sizes
   - Smooth animations with Framer Motion
   - Consistent design system with rounded-2xl cards
   - Loading states and error handling
   - Status badges and icons

### 🚧 In Development

1. **Automation Engine**
   - Web scraping with Selenium/Playwright (infrastructure ready)
   - Mobile app automation with Appium (infrastructure ready)
   - Screenshot capture and processing
   - User interaction simulation

2. **Data Extraction**
   - OCR text extraction from screenshots
   - HTML parsing for web data
   - Flight data normalization
   - Data validation and cleaning

3. **Comparison Logic**
   - Price comparison algorithms
   - Best deal identification
   - Historical price tracking
   - Trend analysis

4. **Error Handling & Monitoring**
   - Comprehensive retry mechanisms
   - Error logging and reporting
   - Performance monitoring
   - Health checks

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user

### Dashboard
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/dashboard/recent-tasks` - Recent tasks
- `GET /api/v1/dashboard/price-trends` - Price trends

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `POST /api/v1/tasks/{id}/start` - Start task
- `POST /api/v1/tasks/{id}/stop` - Stop task
- `GET /api/v1/tasks/{id}/results` - Get task results
- `GET /api/v1/tasks/{id}/export` - Export results

### Platforms
- `GET /api/v1/platforms` - List platforms
- `POST /api/v1/platforms` - Create platform
- `GET /api/v1/platforms/{id}` - Get platform
- `PUT /api/v1/platforms/{id}` - Update platform
- `DELETE /api/v1/platforms/{id}` - Delete platform
- `GET /api/v1/platforms/{id}/accounts` - List accounts
- `POST /api/v1/platforms/{id}/accounts` - Create account

## Database Schema

### Core Tables
- **users**: User authentication and profile data
- **tasks**: Scraping task configurations and status
- **platforms**: Target platforms (websites/apps) configuration
- **accounts**: Platform accounts with credentials
- **flight_data**: Extracted flight information and pricing

## Development Guidelines

### Code Standards
1. **Backend**: Follow PEP 8, use type hints, write docstrings
2. **Frontend**: Use TypeScript, follow React best practices
3. **Testing**: Write unit tests for all business logic
4. **Documentation**: Keep API docs and README updated

### Git Workflow
1. Create feature branches from `main`
2. Write descriptive commit messages
3. Create pull requests for code review
4. Ensure all tests pass before merging

## Deployment

### Production Considerations
1. **Security**: Use environment variables for secrets
2. **Database**: Use managed PostgreSQL service
3. **Monitoring**: Set up logging and error tracking
4. **Scaling**: Configure horizontal scaling for workers
5. **SSL**: Enable HTTPS for all endpoints

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis
REDIS_URL=redis://host:port/0

# Security
SECRET_KEY=your-secret-key

# API Settings
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

## 🚀 Quick Start Checklist

For beginners, follow this checklist to get started:

- [ ] Install Docker and Docker Compose
- [ ] Clone the repository
- [ ] Run `docker-compose up -d`
- [ ] Wait for services to start (2-3 minutes)
- [ ] Run `./test_deployment.sh` to verify installation
- [ ] Create demo user with the provided command
- [ ] Open http://localhost:3000 in your browser
- [ ] Login with `admin` / `admin123`
- [ ] Explore the dashboard and create your first task!

## 📚 Additional Resources

### Documentation
- **API Documentation**: http://localhost:8000/docs (when running)
- **Frontend Components**: Check `frontend/src/components/` for UI components
- **Backend Models**: Check `backend/app/models/` for database schemas

### Useful Commands
```bash
# Check service status
docker-compose ps

# View logs for debugging
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery

# Access database directly
docker-compose exec db psql -U postgres -d flight_scraper

# Access Redis CLI
docker-compose exec redis redis-cli

# Restart specific service
docker-compose restart backend
```

### Development Tips
1. **Hot Reload**: Both frontend and backend support hot reload during development
2. **Database**: Data persists in Docker volumes, use `docker-compose down --volumes` to reset
3. **Logs**: Check logs frequently when debugging issues
4. **API Testing**: Use the built-in API docs at http://localhost:8000/docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Write tests for new functionality
- Update documentation for API changes
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Getting Help
If you encounter issues:

1. **Check the logs**: `docker-compose logs [service-name]`
2. **Run the test script**: `./test_deployment.sh`
3. **Verify all services**: `docker-compose ps`
4. **Check API docs**: http://localhost:8000/docs
5. **Search existing issues**: Check GitHub Issues
6. **Create a new issue**: Provide detailed information about your problem

### Common Solutions
- **Port conflicts**: Change ports in `docker-compose.yml`
- **Build failures**: Run `docker-compose up --build -d`
- **Database issues**: Reset with `docker-compose down --volumes`
- **Permission issues**: Ensure Docker has proper permissions

### Contact
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check this file and README.md
- **Development Team**: Contact through GitHub

---

**Happy coding! 🎉**

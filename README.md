# 🛩️ Flight Data Scraping Tool

A comprehensive web scraping application for flight price monitoring with Android app automation capabilities, featuring a modern React frontend and FastAPI backend.

## 🚀 Features

### ✅ Completed Features
- **Modern Web Interface**: React 18 + TypeScript + TailwindCSS
- **Authentication System**: JWT-based login with secure password hashing
- **Task Management**: Create, monitor, and manage flight scraping tasks
- **Dashboard**: Real-time statistics and task monitoring
- **System Configuration**: Platform settings and account management
- **Docker Deployment**: Complete containerized setup
- **Database Integration**: PostgreSQL with SQLAlchemy ORM
- **Background Processing**: Celery task queue with Redis
- **Toast Notifications**: User-friendly feedback system
- **Android App Automation**: Containerized Android emulator deployment
- **Screenshot Capture**: Automated app testing with screenshot generation
- **Platform Configuration**: Mobile app and website platform management

### 🚧 In Development
- **Web Scraping Engine**: Selenium/Playwright automation
- **Data Extraction**: Flight price parsing and comparison
- **OCR Processing**: Tesseract for screenshot text extraction

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Celery        │    │   Redis         │
│   (Optional)    │    │   Worker        │    │   (Message      │
│   Port: 80      │    │                 │    │    Broker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Android       │
                    │   Automation    │
                    │   Containers    │
                    │   Port: 5555    │
                    └─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Python ORM for database operations
- **PostgreSQL**: Primary database
- **Celery**: Distributed task queue
- **Redis**: Message broker and caching
- **JWT**: Authentication tokens
- **Pydantic**: Data validation
- **Docker**: Containerized Android emulators
- **ADB**: Android Debug Bridge for mobile automation

### Frontend
- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe JavaScript
- **TailwindCSS**: Utility-first CSS framework
- **React Query**: Data fetching and caching
- **Framer Motion**: Smooth animations
- **React Router**: Client-side routing
- **Lucide React**: Beautiful icons

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **GitHub**: Version control and CI/CD

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/lixiaojie/flight-scraper.git
cd flight-scraper
```

### 2. Start the Application
```bash
docker-compose up -d
```

### 3. Verify Installation
```bash
chmod +x test_deployment.sh
./test_deployment.sh
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Create Demo User
```bash
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
try:
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

### 6. Login and Explore
- **Username**: `admin`
- **Password**: `admin123`

## 📁 Project Structure

```
flight-scraper/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Celery tasks
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── contexts/       # React contexts
│   │   └── lib/            # Utilities
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml      # Multi-container setup
├── test_deployment.sh      # Deployment testing
└── SETUP.md               # Detailed setup guide
```

## 🔧 Development

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature development branches

### Development Workflow
1. Create feature branch from `develop`
2. Develop and test features
3. Create pull request to `develop`
4. Merge to `main` for releases

### Local Development
```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend development
cd frontend
npm install
npm run dev

# Celery worker
celery -A app.core.celery worker --loglevel=info
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - User logout

### Tasks
- `GET /api/v1/tasks` - List all tasks
- `POST /api/v1/tasks` - Create new task
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/recent-tasks` - Get recent tasks

## 🧪 Testing

### Run Tests
```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
cd frontend && npm test

# End-to-end deployment test
./test_deployment.sh
```

## 🚀 Deployment

### Production Deployment
1. Update environment variables
2. Configure production database
3. Set up SSL certificates
4. Deploy with Docker Compose

### Environment Variables
See `backend/env.example` and `frontend/env.example` for required environment variables.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See `SETUP.md` for detailed setup instructions
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🎯 Roadmap

- [ ] Complete web scraping engine
- [ ] Mobile app automation
- [ ] Advanced data analytics
- [ ] Real-time notifications
- [ ] Multi-language support
- [ ] API rate limiting
- [ ] Advanced security features

---

**Made with ❤️ for efficient flight price monitoring**
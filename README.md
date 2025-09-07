# Flight Data Scraping Tool

A comprehensive, modern tool for scraping flight booking data from multiple apps and websites. Built with FastAPI and React, it provides automated data collection, price comparison, and a beautiful user interface for managing scraping tasks.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd flight-scraper

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Demo Credentials
- **Username**: `admin`
- **Password**: `admin123`

## ✨ Features

### ✅ Implemented
- **Modern Dashboard**: Real-time task monitoring and statistics
- **Task Management**: Create, schedule, and monitor scraping tasks
- **Platform Configuration**: Manage target platforms and accounts
- **Authentication**: Secure user login and session management
- **Responsive UI**: Beautiful, modern interface with dark mode
- **Real-time Updates**: Live task status and progress tracking
- **Docker Support**: Complete containerized development environment

### 🚧 In Development
- **Web Automation**: Selenium/Playwright integration for website scraping
- **Mobile Automation**: Appium integration for mobile app scraping
- **Data Extraction**: OCR and HTML parsing for flight data
- **Price Comparison**: Automated comparison and best deal identification
- **Export Features**: CSV/Excel export of scraping results

## 🏗️ Architecture

### Backend (Python/FastAPI)
```
backend/
├── app/
│   ├── api/           # REST API endpoints
│   ├── core/          # Configuration, security, database
│   ├── models/        # SQLAlchemy database models
│   ├── services/      # Business logic services
│   └── schemas/       # Pydantic data validation
├── requirements.txt   # Python dependencies
└── main.py           # FastAPI application entry point
```

### Frontend (React/TypeScript)
```
frontend/
├── src/
│   ├── components/    # Reusable UI components
│   ├── pages/         # Page components
│   ├── contexts/      # React contexts (auth, theme)
│   ├── lib/           # Utilities and API client
│   └── types/         # TypeScript type definitions
├── package.json       # Node.js dependencies
└── tailwind.config.js # TailwindCSS configuration
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - Database ORM with PostgreSQL
- **Celery** - Distributed task queue with Redis
- **Pydantic** - Data validation and serialization
- **JWT** - Secure authentication tokens

### Frontend
- **React 18** - Modern UI framework with TypeScript
- **Vite** - Fast build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **ShadCN/UI** - Beautiful component library
- **React Query** - Data fetching and caching
- **Framer Motion** - Smooth animations

### Infrastructure
- **Docker** - Containerization
- **PostgreSQL** - Primary database
- **Redis** - Message broker and caching
- **Nginx** - Reverse proxy (production)

## 📊 Database Schema

### Core Entities
- **Users** - Authentication and user management
- **Tasks** - Scraping task configurations
- **Platforms** - Target platforms (websites/apps)
- **Accounts** - Platform credentials and limits
- **Flight Data** - Extracted flight information

## 🔧 Development

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Local Development Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Configuration
Copy the example environment files and configure:
- `backend/env.example` → `backend/.env`
- `frontend/env.example` → `frontend/.env`

## 📚 API Documentation

### Authentication
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Current user info

### Tasks
- `GET /api/v1/tasks` - List all tasks
- `POST /api/v1/tasks` - Create new task
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

### Dashboard
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/dashboard/recent-tasks` - Recent tasks
- `GET /api/v1/dashboard/price-trends` - Price trends

Full API documentation available at: http://localhost:8000/docs

## 🚀 Deployment

### Production Checklist
- [ ] Set secure `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up SSL certificates
- [ ] Configure environment variables
- [ ] Set up monitoring and logging
- [ ] Configure backup strategies

### Docker Production
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Write tests for new functionality
- Update documentation for API changes
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 **Documentation**: See [SETUP.md](SETUP.md) for detailed setup instructions
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discussions**: Join our GitHub Discussions for questions
- 📧 **Contact**: Reach out to the development team

## 🎯 Roadmap

### Phase 1: Core Platform ✅
- [x] Project architecture and setup
- [x] User authentication and authorization
- [x] Task management system
- [x] Platform configuration
- [x] Modern UI/UX with responsive design

### Phase 2: Automation Engine 🚧
- [ ] Web scraping automation (Selenium/Playwright)
- [ ] Mobile app automation (Appium)
- [ ] Screenshot capture and processing
- [ ] Data extraction and parsing

### Phase 3: Data Processing 🚧
- [ ] OCR text extraction
- [ ] Flight data normalization
- [ ] Price comparison algorithms
- [ ] Export and reporting features

### Phase 4: Advanced Features 📋
- [ ] Machine learning for price prediction
- [ ] Advanced analytics and insights
- [ ] Multi-language support
- [ ] Mobile app development

---

**Built with ❤️ for efficient flight data collection and analysis**

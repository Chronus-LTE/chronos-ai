# 🚀 Quick Start Guide

## Prerequisites Checklist
- [ ] Python 3.11+ installed
- [ ] Docker Desktop installed and running
- [ ] Google Cloud Project created
- [ ] Gemini API key obtained

---

## 🎯 Setup Steps

### 1. Clone and Navigate
```bash
cd /Users/huyphan/Documents/Chronus/chronus-ai
```

### 2. Run Setup Script (Recommended)
```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Start Docker services (PostgreSQL, Redis, Qdrant)
- Run database migrations
- Create .env file

### 3. Configure Environment Variables
Edit `.env` file and add your credentials:
```bash
# Google APIs
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Security (generate a random secret key)
SECRET_KEY=your-secret-key-here
```

### 4. Start the Application
```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start Background Workers (Optional)
In separate terminals:

```bash
# Terminal 2: Celery Worker
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3: Celery Beat (Scheduler)
source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info

# Terminal 4: Flower (Monitoring)
source venv/bin/activate
celery -A app.tasks.celery_app flower --port=5555
```

---

## 🌐 Access Points

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Flower (Celery Monitor)**: http://localhost:5555

---

## 🧪 Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_main.py -v
```

---

## 🛠️ Development Commands

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current
```

### Docker Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart a specific service
docker-compose restart postgres
```

### Code Quality
```bash
# Format code with Black
black app/

# Lint with Flake8
flake8 app/

# Type checking with MyPy
mypy app/
```

---

## 📊 Project Status

### ✅ Completed
- [x] Project structure setup
- [x] FastAPI application skeleton
- [x] Database configuration (PostgreSQL)
- [x] Redis integration
- [x] Qdrant setup
- [x] Docker Compose configuration
- [x] Alembic migrations setup
- [x] Basic tests

### 🚧 In Progress
- [ ] User authentication
- [ ] Google Calendar integration
- [ ] Google Tasks integration
- [ ] Gmail integration
- [ ] Gemini AI agent
- [ ] Vector store service

### 📋 TODO
- [ ] Celery tasks implementation
- [ ] API endpoints
- [ ] Frontend (optional)
- [ ] Deployment configuration

---

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres
```

### Redis Connection Error
```bash
# Check if Redis is running
docker-compose ps

# Restart Redis
docker-compose restart redis
```

### Import Errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📚 Next Steps

1. **Implement User Model** - Create user authentication
2. **Google OAuth** - Setup Google API authentication
3. **Calendar Service** - Implement calendar sync
4. **Task Service** - Implement task management
5. **Email Service** - Implement email digest
6. **AI Agent** - Setup Gemini with function calling
7. **Vector Store** - Implement memory and semantic search

---

## 💡 Tips

- Use `--reload` flag during development for auto-reload
- Check logs in `docker-compose logs -f` for debugging
- Use Swagger UI at `/docs` for API testing
- Monitor Celery tasks with Flower
- Keep your `.env` file secure and never commit it

---

**Happy Building! 🚀**

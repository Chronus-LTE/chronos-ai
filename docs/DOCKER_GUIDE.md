# 🐳 Chronus AI - Docker Complete Guide

## 🎯 Overview

Bây giờ **TẤT CẢ** services chạy trong Docker! Bạn **KHÔNG CẦN** cài Python local nữa! 🎉

### Services trong Docker:
1. ✅ **PostgreSQL** - Database
2. ✅ **Redis** - Cache & Queue
3. ✅ **Qdrant** - Vector Database
4. ✅ **FastAPI** - API Server
5. ✅ **Celery Worker** - Background tasks
6. ✅ **Celery Beat** - Task scheduler
7. ✅ **Flower** - Celery monitoring

---

## 🚀 Quick Start (3 Steps)

### 1️⃣ Setup Environment
```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

### 2️⃣ Start Everything
```bash
# Option A: Using script (Recommended)
./docker-start.sh

# Option B: Using Make
make dev

# Option C: Manual
docker-compose up -d
```

### 3️⃣ Access Your App
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant**: http://localhost:6333/dashboard
- **Flower**: http://localhost:5555

---

## 📋 Available Commands

### Using Scripts (Easy)

```bash
# Start all services
./docker-start.sh

# Stop all services
./docker-stop.sh

# View logs
./docker-logs.sh
```

### Using Make (Recommended)

```bash
# Show all available commands
make help

# Start development environment
make dev

# Start services
make up

# Stop services
make down

# View logs
make logs

# Check status
make status

# Run migrations
make migrate

# Open shell in API container
make shell

# Run tests
make test

# Format code
make format
```

### Using Docker Compose (Manual)

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart a service
docker-compose restart api

# View logs for specific service
docker-compose logs -f api
```

---

## 🔧 Common Tasks

### Run Database Migrations
```bash
# Using Make
make migrate

# Using Docker Compose
docker-compose exec api alembic upgrade head

# Create new migration
make migrate-create MSG="add user table"
```

### Access Database
```bash
# Using Make
make shell-db

# Using Docker Compose
docker-compose exec postgres psql -U chronus -d chronus_db
```

### Access API Container Shell
```bash
# Using Make
make shell

# Using Docker Compose
docker-compose exec api /bin/bash
```

### Run Tests
```bash
# Using Make
make test

# With coverage
make test-cov

# Using Docker Compose
docker-compose exec api pytest
```

### View Logs
```bash
# All services
make logs

# Specific service
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f postgres
```

### Restart Services
```bash
# All services
make restart

# Specific service
docker-compose restart api
docker-compose restart celery-worker
```

---

## 🗂️ Docker Compose Services

### Service Details

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| postgres | chronus-postgres | 5432 | PostgreSQL database |
| redis | chronus-redis | 6379 | Redis cache & queue |
| qdrant | chronus-qdrant | 6333, 6334 | Vector database |
| api | chronus-api | 8000 | FastAPI application |
| celery-worker | chronus-celery-worker | - | Background task worker |
| celery-beat | chronus-celery-beat | - | Task scheduler |
| flower | chronus-flower | 5555 | Celery monitoring |

### Service Dependencies

```
api → postgres, redis, qdrant
celery-worker → postgres, redis, qdrant
celery-beat → postgres, redis
flower → redis, celery-worker
```

---

## 🔍 Debugging

### Check Service Status
```bash
docker-compose ps
```

### View Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f postgres
```

### Check Service Health
```bash
# API health check
curl http://localhost:8000/health

# Qdrant health check
curl http://localhost:6333/healthz

# PostgreSQL
docker-compose exec postgres pg_isready -U chronus

# Redis
docker-compose exec redis redis-cli ping
```

### Restart Problematic Service
```bash
docker-compose restart api
docker-compose restart celery-worker
```

### Rebuild Service
```bash
# Rebuild specific service
docker-compose build api

# Rebuild all services
docker-compose build

# Rebuild and restart
docker-compose up -d --build
```

---

## 🧹 Cleanup

### Stop Services (Keep Data)
```bash
make down
# or
docker-compose down
```

### Stop Services + Remove Volumes (Delete Data)
```bash
make clean
# or
docker-compose down -v
```

### Remove All Docker Resources
```bash
# Stop and remove everything
docker-compose down -v

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

---

## 🔄 Development Workflow

### Daily Development
```bash
# 1. Start services
make up

# 2. View logs (optional)
make logs

# 3. Code changes are auto-reloaded (FastAPI --reload)

# 4. Run tests
make test

# 5. Stop when done
make down
```

### After Code Changes
```bash
# FastAPI auto-reloads, no restart needed!
# But if you change dependencies:

# 1. Rebuild
docker-compose build api

# 2. Restart
docker-compose up -d api
```

### After Database Model Changes
```bash
# 1. Create migration
make migrate-create MSG="add new field"

# 2. Apply migration
make migrate

# 3. Verify
make shell-db
# Then: \dt to list tables
```

---

## 📊 Monitoring

### Flower (Celery Tasks)
- URL: http://localhost:5555
- Monitor background tasks
- View task history
- See worker status

### Qdrant Dashboard
- URL: http://localhost:6333/dashboard
- View collections
- Search vectors
- Monitor performance

### API Docs
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Container Won't Start
```bash
# View logs
docker-compose logs <service-name>

# Check if port is available
lsof -i :<port>

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Database Connection Error
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### Celery Worker Not Processing Tasks
```bash
# Check worker logs
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Out of Disk Space
```bash
# Remove unused Docker resources
docker system prune -a

# Remove volumes
docker volume prune
```

---

## 🔐 Environment Variables

### Required in .env:
```bash
# Google APIs
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Security
SECRET_KEY=your-secret-key
```

### Auto-configured by Docker Compose:
- DATABASE_URL
- REDIS_URL
- QDRANT_HOST
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND

---

## 📦 Data Persistence

### Volumes (Data is Preserved)
- `postgres_data` - Database data
- `redis_data` - Redis data
- `qdrant_data` - Vector data

### To Backup Data
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U chronus chronus_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U chronus chronus_db < backup.sql
```

---

## 🚀 Production Deployment

### Build for Production
```bash
# Build optimized images
docker-compose -f docker-compose.prod.yml build

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production
```bash
# In .env
ENVIRONMENT=production
DEBUG=False

# Use managed databases
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

---

## 💡 Pro Tips

1. **Use Make commands** - Faster and easier than docker-compose
2. **Check logs regularly** - `make logs` to catch errors early
3. **Use health checks** - Built into docker-compose
4. **Volume mounts** - Code changes auto-reload
5. **Network isolation** - All services in `chronus-network`

---

## 📚 Cheat Sheet

```bash
# Quick Reference
make help          # Show all commands
make dev           # Start everything
make logs          # View logs
make status        # Check status
make shell         # Open API shell
make test          # Run tests
make migrate       # Run migrations
make down          # Stop all
make clean         # Remove all + data
```

---

## ✅ Advantages of This Setup

- ✅ **No Python installation needed** - Everything in Docker
- ✅ **Consistent environment** - Same for all developers
- ✅ **Easy to start** - One command: `make dev`
- ✅ **Auto-reload** - Code changes reflected immediately
- ✅ **Isolated** - No conflicts with other projects
- ✅ **Production-ready** - Same setup for dev and prod
- ✅ **Easy cleanup** - `make clean` removes everything

---

**Bây giờ bạn chỉ cần Docker! Không cần cài Python, PostgreSQL, Redis gì cả! 🎉**

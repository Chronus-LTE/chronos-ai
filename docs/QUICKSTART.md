# 🚀 Quick Start Guide - Chronus AI

## 📋 Prerequisites

- Docker & Docker Compose
- Google OAuth credentials
- Gemini API key

---

## 🔧 Setup

### 1. Clone & Configure

```bash
cd /Users/huyphan/Documents/Chronus/chronus-ai

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Required Environment Variables

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Gemini API
GEMINI_API_KEY=your-gemini-api-key-here

# Security
SECRET_KEY=your-random-secret-key-here

# Database (default - no need to change)
DATABASE_URL=postgresql+asyncpg://chronus:chronus123@postgres:5432/chronus

# Redis (default)
REDIS_URL=redis://redis:6379/0

# Qdrant (default)
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Celery (default)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## 🐳 Start Services

### Option 1: Start All Services

```bash
docker-compose up -d
```

### Option 2: Start Specific Services

```bash
# Core services only
docker-compose up -d postgres redis api

# Add Celery for proactive analysis
docker-compose up -d celery-worker celery-beat

# Add Qdrant for vector search
docker-compose up -d qdrant

# Add Flower for monitoring
docker-compose up -d flower
```

---

## 📊 Check Services

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery-worker
```

### Check Status

```bash
docker-compose ps
```

### Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery)**: http://localhost:5555
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## 🗄️ Database Setup

### Run Migrations

```bash
# Enter API container
docker-compose exec api bash

# Run migrations
alembic upgrade head

# Exit container
exit
```

---

## ✅ Test the System

### 1. Test API Health

```bash
curl http://localhost:8000/
```

### 2. Test Google OAuth

1. Open: http://localhost:8000/static/login.html
2. Click "Login with Google"
3. Authorize the app
4. You'll be redirected to dashboard

### 3. Test Gmail Integration

1. Login first (step 2)
2. Open: http://localhost:8000/static/gmail-test.html
3. Test các features:
   - List emails
   - Search emails
   - Send email
   - Create draft

### 4. Test AI Agent

```bash
# Get your JWT token from browser localStorage after login
TOKEN="your-jwt-token"

# Test chat
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tôi có email chưa đọc không?"}'
```

### 5. Test Alerts

```bash
# List alerts
curl http://localhost:8000/api/v1/alerts/ \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Test Knowledge Base

```bash
# Create knowledge
curl -X POST http://localhost:8000/api/v1/knowledge/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "How to use Chronus",
    "content": "Chronus is an AI assistant...",
    "category": "tutorial"
  }'

# Search knowledge
curl "http://localhost:8000/api/v1/knowledge/search?query=how+to+use" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔍 Monitoring

### Celery Tasks (Flower)

```bash
open http://localhost:5555
```

### Qdrant Collections

```bash
curl http://localhost:6333/collections
```

### Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U chronus -d chronus

# List tables
\dt

# Exit
\q
```

---

## 🛠️ Common Commands

### Restart Services

```bash
docker-compose restart api
docker-compose restart celery-worker
```

### View Service Logs

```bash
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
```

### Stop All Services

```bash
docker-compose down
```

### Clean Up (⚠️ Deletes all data)

```bash
docker-compose down -v
```

---

## 🐛 Troubleshooting

### API not starting?

```bash
# Check logs
docker-compose logs api

# Rebuild
docker-compose build api
docker-compose up -d api
```

### Celery tasks not running?

```bash
# Check Celery worker
docker-compose logs celery-worker

# Check Celery beat
docker-compose logs celery-beat

# Restart
docker-compose restart celery-worker celery-beat
```

### Qdrant connection error?

```bash
# Check Qdrant status
curl http://localhost:6333/collections

# Restart Qdrant
docker-compose restart qdrant
```

### Database migration issues?

```bash
# Enter container
docker-compose exec api bash

# Check current version
alembic current

# Upgrade
alembic upgrade head

# Or downgrade if needed
alembic downgrade -1
```

---

## 📚 Next Steps

1. ✅ **Test Gmail Integration**

   - Login with Google
   - Test reading emails
   - Test sending emails
   - Test draft functionality

2. ✅ **Test Proactive Analysis**

   - Wait for daily analysis (or trigger manually)
   - Check alerts: http://localhost:8000/api/v1/alerts/

3. ✅ **Test Knowledge Base**

   - Create some knowledge entries
   - Test semantic search
   - Use in AI chat

4. ✅ **Monitor Celery**
   - Open Flower: http://localhost:5555
   - Check task execution
   - Monitor workers

---

## 🎯 Quick Reference

### Service Ports

- API: 8000
- PostgreSQL: 5432
- Redis: 6379
- Qdrant: 6333, 6334
- Flower: 5555

### Important URLs

- API Docs: http://localhost:8000/docs
- Login: http://localhost:8000/static/login.html
- Dashboard: http://localhost:8000/static/dashboard.html
- Gmail Test: http://localhost:8000/static/gmail-test.html
- Flower: http://localhost:5555

### Default Credentials

- PostgreSQL: chronus / chronus123
- Database: chronus

---

## 🚀 You're Ready!

Tất cả services đã sẵn sàng! Bắt đầu test và develop thôi! 🎉

**Need help?** Check:

- API Docs: http://localhost:8000/docs
- Implementation Summary: `docs/IMPLEMENTATION_SUMMARY.md`
- Gmail Integration: `docs/GMAIL_INTEGRATION.md`

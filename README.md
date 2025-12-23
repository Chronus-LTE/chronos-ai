# Chronus AI Backend

A powerful FastAPI backend providing Gmail integration, Google Calendar sync, and AI-powered features for the Chronus productivity suite.

## 🌟 Features

### 📧 Gmail Integration

- **Full Gmail Sync**: Initial and incremental sync with history tracking
- **Email Operations**: Read, send, delete, star, mark read/unread
- **Advanced Search**: Search emails with Gmail query syntax
- **Label Management**: Support for Gmail labels and folders
- **Attachment Handling**: Download and manage email attachments
- **Batch Operations**: Efficient bulk email processing

### 📅 Google Calendar

- **Calendar Sync**: Sync events from Google Calendar
- **Event Management**: Create, update, delete calendar events
- **Multiple Calendars**: Support for multiple calendar sources

### 🤖 AI Features

- **Proactive Analysis**: AI-powered email and calendar insights
- **Smart Suggestions**: Context-aware recommendations
- **Background Tasks**: Celery-based async processing

### 🔐 Authentication

- **Google OAuth 2.0**: Secure authentication with Google
- **JWT Tokens**: Stateless authentication
- **Refresh Token Management**: Automatic token refresh

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 6 or higher (for Celery)
- **Google Cloud Project**: With OAuth 2.0 credentials

### Installation

1. **Clone the repository**

   ```bash
   cd chronus-ai
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create `.env` file:

   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/chronus

   # Google OAuth
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret

   # JWT
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Redis (for Celery)
   REDIS_URL=redis://localhost:6379/0

   # AI (Optional)
   OPENAI_API_KEY=your-openai-key
   ```

5. **Set up database**

   ```bash
   # Create database
   createdb chronus

   # Run migrations
   alembic upgrade head
   ```

6. **Run the server**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Run Celery worker** (in separate terminal)
   ```bash
   celery -A app.tasks worker --loglevel=info
   ```

## 📁 Project Structure

```
app/
├── api/
│   └── v1/
│       ├── auth.py          # Authentication endpoints
│       ├── gmail.py         # Gmail API endpoints
│       └── calendar.py      # Calendar endpoints
├── models/
│   ├── user.py             # User model
│   ├── email.py            # Email models
│   └── alert.py            # Alert models
├── schemas/
│   ├── auth.py             # Auth schemas
│   ├── gmail.py            # Gmail schemas
│   └── __init__.py
├── services/
│   ├── auth/               # Authentication services
│   ├── google/             # Google API services
│   ├── ai/                 # AI services
│   └── email_sync_service.py
├── tasks/
│   ├── gmail_sync_tasks.py # Celery tasks for Gmail
│   └── proactive_tasks.py  # AI analysis tasks
├── utils/
│   └── jwt_utils.py        # JWT utilities
├── database.py             # Database configuration
└── main.py                 # FastAPI application
```

## 🔧 API Endpoints

### Authentication

```
POST   /api/v1/auth/register          # Register new user
POST   /api/v1/auth/login             # Login with email/password
POST   /api/v1/auth/google/mobile     # Google Sign-In (mobile)
GET    /api/v1/auth/me                # Get current user
```

### Gmail

```
# Sync
POST   /api/v1/gmail/sync             # Start email sync
GET    /api/v1/gmail/sync/status      # Get sync status

# Emails
GET    /api/v1/gmail/emails           # List emails (with filters)
GET    /api/v1/gmail/emails/{id}      # Get email detail
GET    /api/v1/gmail/search           # Search emails
POST   /api/v1/gmail/send             # Send email
DELETE /api/v1/gmail/emails/{id}      # Delete email

# Actions
POST   /api/v1/gmail/emails/{id}/mark-read    # Mark as read
POST   /api/v1/gmail/emails/{id}/mark-unread  # Mark as unread
POST   /api/v1/gmail/emails/{id}/star         # Star email
POST   /api/v1/gmail/emails/{id}/unstar       # Unstar email

# Metadata
GET    /api/v1/gmail/unread-count     # Get unread count
```

### Calendar

```
GET    /api/v1/calendar/events        # List calendar events
POST   /api/v1/calendar/events        # Create event
PUT    /api/v1/calendar/events/{id}   # Update event
DELETE /api/v1/calendar/events/{id}   # Delete event
```

## 🗄️ Database Schema

### Users Table

```sql
- id (string, primary key)
- email (string, unique)
- name (string)
- google_access_token (string)
- google_refresh_token (string)
- created_at (timestamp)
```

### Emails Table

```sql
- id (integer, primary key)
- gmail_id (string, unique)
- thread_id (string)
- user_id (string, foreign key)
- subject (string)
- from_email (string)
- to_email (string)
- body_html (text)
- body_plain (text)
- date (timestamp)
- labels (jsonb array)
- is_unread (boolean)
- is_starred (boolean)
- has_attachments (boolean)
```

### Gmail Sync State Table

```sql
- id (integer, primary key)
- user_id (string, unique)
- status (string)
- sync_type (string)
- total_messages (integer)
- synced_messages (integer)
- history_id (string)
- last_sync_date (timestamp)
```

## 🔐 Google OAuth Setup

1. **Create Google Cloud Project**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project

2. **Enable APIs**

   - Gmail API
   - Google Calendar API
   - Google Tasks API

3. **Create OAuth 2.0 Credentials**

   - Application type: Web application
   - Authorized redirect URIs:
     - `http://localhost:8000/api/v1/auth/google/callback`
     - Your production domain

4. **Configure Consent Screen**

   - Add required scopes
   - Add test users (for development)

5. **Download credentials**
   - Save client ID and client secret to `.env`

## 🏗️ Architecture

### Design Patterns

- **Repository Pattern**: Service layer for business logic
- **Dependency Injection**: FastAPI dependencies
- **Background Tasks**: Celery for async processing

### Database

- **PostgreSQL**: Primary database
- **SQLAlchemy**: ORM
- **Alembic**: Database migrations

### Caching & Queue

- **Redis**: Celery broker and result backend

### Performance Optimizations

- **Incremental Sync**: Only sync new/changed emails
- **Batch Processing**: Process emails in batches
- **Database Indexing**: Optimized queries
- **Connection Pooling**: Reuse database connections

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_gmail.py
```

## 🚀 Deployment

### Using Docker

```bash
# Build image
docker build -t chronus-ai .

# Run container
docker run -p 8000:8000 --env-file .env chronus-ai
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Use production database
- [ ] Enable HTTPS
- [ ] Set up proper CORS
- [ ] Configure rate limiting
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Enable database backups
- [ ] Use environment-specific configs

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics

- API response times
- Database query performance
- Celery task queue length
- Email sync success rate

## 🐛 Troubleshooting

### Common Issues

**Database connection errors**

```bash
# Check PostgreSQL is running
pg_isready

# Check connection string
echo $DATABASE_URL
```

**Google OAuth errors**

- Verify client ID and secret
- Check redirect URIs match
- Ensure APIs are enabled

**Celery tasks not running**

```bash
# Check Redis is running
redis-cli ping

# Check Celery worker
celery -A app.tasks inspect active
```

**Email sync fails**

- Check Google API quotas
- Verify refresh token is valid
- Check user has granted permissions

## 📦 Dependencies

### Core

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `alembic` - Database migrations
- `pydantic` - Data validation

### Google APIs

- `google-auth` - Google authentication
- `google-api-python-client` - Google API client

### Background Tasks

- `celery` - Task queue
- `redis` - Message broker

### Database

- `psycopg2-binary` - PostgreSQL adapter
- `asyncpg` - Async PostgreSQL

### AI (Optional)

- `openai` - OpenAI API client
- `langchain` - LLM framework

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Rate limiting
- SQL injection prevention (SQLAlchemy)
- XSS protection

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Write tests
4. Submit pull request

## 🔗 Related Repositories

- [Chronos Mobile](../chronos-mobile) - Flutter mobile app
- [Chronus Web App](../chronus-webapp) - Angular web app

---

**Built with FastAPI and ❤️**

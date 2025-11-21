# 🤖 Chronus AI - Your Personal AI Assistant

## **Chronus AI** is an intelligent personal assistant that helps you manage your calendar, tasks, and emails using AI-powered automation and proactive suggestions.

## ✨ Features

### 📅 Calendar Integration

- Sync with Google Calendar
- Smart event reminders (5-10 minutes before)
- Analyze free time slots for side projects
- Auto-create events from natural language
- Conflict detection and overload warnings

### ✅ Task Management

- Integration with Google Tasks
- Voice and chat-based task creation
- Priority management by deadline and project
- Sync tasks with calendar
- Daily task overview with priorities

### 📧 Email Intelligence

- Gmail integration (read-only + labels)
- Daily email digest (important & unread)
- Auto-extract action items from emails
- Follow-up reminders for unanswered emails

### 🧠 Memory & Habits

- Learn your preferences and habits
- Track weekly/monthly progress
- Context-aware suggestions
- Semantic search across tasks and emails

### 🎯 Proactive Suggestions

- Smart scheduling recommendations
- Workload balancing
- Habit tracking and reminders

---

## 🏗️ Tech Stack

### Backend

- **Python 3.11+** - Core language
- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM for PostgreSQL
- **PostgreSQL** - Primary database
- **Redis** - Caching and message queue
- **Celery** - Background task processing

### AI & Vector Database

- **Google Gemini API** - Large Language Model
- **Qdrant** - Vector database for semantic search
- **sentence-transformers** - Text embeddings

### Integrations

- **Google Calendar API**
- **Google Tasks API**
- **Gmail API**

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (Required)
- Google Cloud Project with APIs enabled
- Gemini API key

**Note**: You DON'T need to install Python, PostgreSQL, or Redis locally! Everything runs in Docker! 🐳

### 3 Simple Steps

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env and add your API keys

# 2. Start everything
./scripts/docker-start.sh

# Or using Make
make dev

# 3. Done! Visit http://localhost:8000/docs
```

**That's it!** All services are now running! 🎉

---

## 🌐 Access Points

Once running, you'll have:

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Flower (Celery Monitor)**: http://localhost:5555

---

## 📁 Project Structure

```
chronus-ai/
├── 📄 README.md                    # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 docker-compose.yml           # Docker services
├── 📄 Dockerfile                   # Container image
├── 📄 Makefile                     # Quick commands
├── 📄 alembic.ini                  # Migration config
├── 🔒 .env.example                 # Environment template
│
├── 📚 docs/                        # Documentation
│   ├── DOCKER_GUIDE.md             # Complete Docker guide
│   ├── QUICKSTART.md               # Quick setup guide
│   ├── TECH_STACK.md               # Tech stack details
│   ├── ARCHITECTURE.md             # System architecture
│   └── PROJECT_SETUP.md            # Setup summary
│
├── 🔧 scripts/                     # Utility scripts
│   ├── docker-start.sh             # Start all services
│   ├── docker-stop.sh              # Stop all services
│   ├── docker-logs.sh              # View logs
│   └── setup.sh                    # Local Python setup
│
├── 📦 app/                         # Main application
│   ├── main.py                     # FastAPI entry point
│   ├── config.py                   # Settings
│   ├── database.py                 # DB connection
│   │
│   ├── models/                     # SQLAlchemy models
│   ├── schemas/                    # Pydantic schemas
│   │
│   ├── api/                        # API endpoints
│   │   └── v1/                     # API version 1
│   │
│   ├── services/                   # Business logic
│   │   ├── google/                 # Google APIs
│   │   └── ai/                     # AI services
│   │
│   ├── tasks/                      # Celery tasks
│   └── utils/                      # Utilities
│
├── 🗄️ alembic/                     # Database migrations
│   ├── env.py                      # Alembic config
│   └── versions/                   # Migration files
│
└── 🧪 tests/                       # Test suite
    ├── conftest.py                 # Pytest config
    └── test_main.py                # Example tests
```

---

## 📚 Documentation

| Document                                  | Description                                             |
| ----------------------------------------- | ------------------------------------------------------- |
| [DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md)   | **⭐ Complete Docker guide** - All commands & workflows |
| [QUICKSTART.md](docs/QUICKSTART.md)       | Quick setup guide with step-by-step instructions        |
| [TECH_STACK.md](docs/TECH_STACK.md)       | Detailed tech stack and architecture decisions          |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)   | System architecture diagrams and data flows             |
| [PROJECT_SETUP.md](docs/PROJECT_SETUP.md) | Setup completion summary and quick reference            |

---

## 🛠️ Quick Commands

### Using Scripts

```bash
# Start all services
./scripts/docker-start.sh

# Stop all services
./scripts/docker-stop.sh

# View logs
./scripts/docker-logs.sh
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

# Run tests
make test

# Open shell in API container
make shell

# Format code
make format
```

See [Makefile](Makefile) for all available commands.

---

## 🐳 Docker Services

Your `docker-compose.yml` includes:

| Service           | Port | Description            |
| ----------------- | ---- | ---------------------- |
| **postgres**      | 5432 | PostgreSQL database    |
| **redis**         | 6379 | Redis cache & queue    |
| **qdrant**        | 6333 | Vector database        |
| **api**           | 8000 | FastAPI application    |
| **celery-worker** | -    | Background task worker |
| **celery-beat**   | -    | Task scheduler         |
| **flower**        | 5555 | Celery monitoring      |

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## 🔧 Configuration

### Google Cloud Setup

1. **Create a Google Cloud Project**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable APIs**

   - Google Calendar API
   - Google Tasks API
   - Gmail API

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Create OAuth 2.0 Client ID
   - Add authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`
   - Download credentials and update `.env`

### Gemini API Setup

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to `.env`: `GEMINI_API_KEY=your-key-here`

### Environment Variables

Edit `.env` file:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Security (generate a random string)
SECRET_KEY=your-secret-key-here
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
docker-compose exec api pytest tests/test_main.py
```

---

## 🛣️ Roadmap

### Phase 1: MVP ✅

- [x] Project setup
- [x] Docker configuration
- [ ] Google Calendar integration
- [ ] Google Tasks integration
- [ ] Gmail integration
- [ ] Basic AI chat with Gemini
- [ ] Vector store for memory

### Phase 2: Intelligence

- [ ] Proactive suggestions
- [ ] Habit tracking
- [ ] Email intelligence
- [ ] Smart scheduling

### Phase 3: Advanced

- [ ] Voice interface
- [ ] Mobile app
- [ ] Self-hosting option
- [ ] Advanced analytics

---

## 🐛 Troubleshooting

### Services won't start?

```bash
# Check Docker is running
docker info

# Check logs
make logs

# Restart services
make restart
```

### Port already in use?

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database connection error?

```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### Need fresh start?

```bash
# Remove everything including data
make clean

# Start fresh
make dev
```

See [DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md) for more troubleshooting tips.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 👤 Author

**Huy Phan**
**Hoang Nguyen**

---

## 🙏 Acknowledgments

- Google Gemini API
- FastAPI framework
- Qdrant vector database
- Open source community

---

## 📞 Support

For issues and questions:

- 📖 Check [DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md)
- 🐛 Open an issue on GitHub
- 💬 Start a discussion

---

## 🎯 Next Steps

1. ✅ Read [DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md) for complete Docker guide
2. ✅ Configure your `.env` file with API keys
3. ✅ Run `make dev` to start all services
4. ✅ Visit http://localhost:8000/docs to explore the API
5. ⏳ Start implementing features!

---

**Built with ❤️ for personal productivity**

🚀 **Ready to start?** Run `make dev` and visit http://localhost:8000/docs

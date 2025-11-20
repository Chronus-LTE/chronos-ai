# 🔧 Chronus AI - Scripts

This folder contains utility scripts to help you manage the Chronus AI application.

---

## 📜 Available Scripts

### 🐳 Docker Scripts

#### `docker-start.sh`
**Start all services with Docker**

```bash
./scripts/docker-start.sh
```

**What it does:**
- ✅ Checks if Docker is running
- ✅ Creates `.env` if missing
- ✅ Stops existing containers
- ✅ Builds Docker images
- ✅ Starts all services
- ✅ Runs database migrations
- ✅ Shows service status

**Services started:**
- PostgreSQL (port 5432)
- Redis (port 6379)
- Qdrant (port 6333)
- FastAPI (port 8000)
- Celery Worker
- Celery Beat
- Flower (port 5555)

---

#### `docker-stop.sh`
**Stop all services**

```bash
./scripts/docker-stop.sh
```

**What it does:**
- ✅ Stops all running containers
- ✅ Keeps data volumes intact

**To remove volumes too:**
```bash
docker-compose down -v
```

---

#### `docker-logs.sh`
**View logs from all services**

```bash
./scripts/docker-logs.sh
```

**What it does:**
- ✅ Shows logs from all containers
- ✅ Follows log output (live updates)
- ✅ Press Ctrl+C to exit

**View logs for specific service:**
```bash
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f postgres
```

---

### 🐍 Python Scripts

#### `setup.sh`
**Setup local Python development environment**

```bash
./scripts/setup.sh
```

**What it does:**
- ✅ Checks Python version (3.11+)
- ✅ Creates virtual environment
- ✅ Installs dependencies
- ✅ Creates `.env` file
- ✅ Starts Docker services
- ✅ Runs database migrations

**Note:** This is optional if you're using Docker for everything.

---

## 🚀 Quick Reference

### Start Everything
```bash
./scripts/docker-start.sh
```

### Stop Everything
```bash
./scripts/docker-stop.sh
```

### View Logs
```bash
./scripts/docker-logs.sh
```

### Setup Local Python (Optional)
```bash
./scripts/setup.sh
```

---

## 💡 Tips

1. **All scripts are executable** - Just run `./scripts/script-name.sh`
2. **Use Docker scripts** - Easiest way to run everything
3. **Check logs** - Use `docker-logs.sh` to debug issues
4. **Scripts are safe** - They won't delete your data unless you use `docker-compose down -v`

---

## 🔧 Making Scripts Executable

If scripts aren't executable:

```bash
chmod +x scripts/*.sh
```

---

## 📝 Script Details

### docker-start.sh
- **Lines**: ~50
- **Dependencies**: Docker
- **Safe to run**: Yes
- **Idempotent**: Yes (can run multiple times)

### docker-stop.sh
- **Lines**: ~10
- **Dependencies**: Docker
- **Safe to run**: Yes
- **Data loss**: No (keeps volumes)

### docker-logs.sh
- **Lines**: ~5
- **Dependencies**: Docker
- **Safe to run**: Yes
- **Interactive**: Yes (Ctrl+C to exit)

### setup.sh
- **Lines**: ~80
- **Dependencies**: Python 3.11+, Docker
- **Safe to run**: Yes
- **Idempotent**: Yes

---

## 🐛 Troubleshooting

### Script won't run
```bash
# Make it executable
chmod +x scripts/docker-start.sh

# Run it
./scripts/docker-start.sh
```

### Docker not found
```bash
# Check if Docker is installed
docker --version

# Start Docker Desktop
# Then try again
```

### Permission denied
```bash
# Make all scripts executable
chmod +x scripts/*.sh
```

---

## 🎯 When to Use Each Script

| Scenario | Script |
|----------|--------|
| First time setup | `docker-start.sh` |
| Daily development start | `docker-start.sh` |
| End of day | `docker-stop.sh` |
| Debugging issues | `docker-logs.sh` |
| Local Python setup | `setup.sh` |

---

## 📚 Related Documentation

- [DOCKER_GUIDE.md](../docs/DOCKER_GUIDE.md) - Complete Docker guide
- [QUICKSTART.md](../docs/QUICKSTART.md) - Quick setup guide
- [README.md](../README.md) - Main documentation

---

**Happy Scripting! 🚀**

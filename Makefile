# Chronus AI - Makefile
# Quick commands for development

.PHONY: help build up down restart logs status clean migrate shell test

help: ## Show this help message
	@echo "Chronus AI - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "🌐 API: http://localhost:8000/docs"

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs (follow mode)
	docker-compose logs -f

status: ## Show service status
	docker-compose ps

clean: ## Stop and remove all containers, volumes
	docker-compose down -v
	@echo "✅ All containers and volumes removed!"

migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	docker-compose exec api alembic revision --autogenerate -m "$(MSG)"

shell: ## Open shell in API container
	docker-compose exec api /bin/bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U chronus -d chronus_db

test: ## Run tests
	docker-compose exec api pytest

test-cov: ## Run tests with coverage
	docker-compose exec api pytest --cov=app tests/

format: ## Format code with Black
	docker-compose exec api black app/

lint: ## Lint code with Flake8
	docker-compose exec api flake8 app/

dev: ## Start in development mode (build + up + logs)
	@echo "🚀 Starting Chronus AI in development mode..."
	@./scripts/docker-start.sh

stop: ## Stop all services (alias for down)
	@./scripts/docker-stop.sh

view-logs: ## View logs using script
	@./scripts/docker-logs.sh

docs: ## Open documentation
	@echo "📚 Documentation:"
	@echo "  - Docker Guide:    docs/DOCKER_GUIDE.md"
	@echo "  - Quick Start:     docs/QUICKSTART.md"
	@echo "  - Tech Stack:      docs/TECH_STACK.md"
	@echo "  - Architecture:    docs/ARCHITECTURE.md"
	@echo "  - Project Setup:   docs/PROJECT_SETUP.md"


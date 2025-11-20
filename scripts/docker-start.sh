#!/bin/bash

# Chronus AI - Docker Start Script
# This script helps you start all services with Docker

set -e

echo "🐳 Chronus AI - Docker Start Script"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "   Please start Docker Desktop and try again."
    exit 1
fi
echo "✅ Docker is running"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env and add your API keys before continuing!"
    echo ""
    read -p "Press Enter to continue after editing .env, or Ctrl+C to exit..."
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down
echo ""

# Build images
echo "🔨 Building Docker images..."
docker-compose build
echo ""

# Start services
echo "🚀 Starting all services..."
docker-compose up -d
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10
echo ""

# Check service status
echo "📊 Service Status:"
docker-compose ps
echo ""

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec api alembic upgrade head
echo ""

echo "===================================="
echo "✅ All services started successfully!"
echo ""
echo "🌐 Access Points:"
echo "   • API:              http://localhost:8000"
echo "   • API Docs:         http://localhost:8000/docs"
echo "   • Qdrant Dashboard: http://localhost:6333/dashboard"
echo "   • Flower (Celery):  http://localhost:5555"
echo ""
echo "📝 Useful Commands:"
echo "   • View logs:        docker-compose logs -f"
echo "   • Stop services:    docker-compose down"
echo "   • Restart:          docker-compose restart"
echo "   • View status:      docker-compose ps"
echo ""
echo "Happy coding! 🚀"

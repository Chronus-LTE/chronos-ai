#!/bin/bash

# Chronus AI - Setup Script
# This script helps you set up the development environment

set -e

echo "🤖 Chronus AI - Setup Script"
echo "================================"
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if Python 3.11+
required_version="3.11"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11 or higher is required"
    exit 1
fi
echo "   ✅ Python version OK"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo "   ℹ️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

# Create .env file
echo "⚙️  Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ✅ .env file created from .env.example"
    echo "   ⚠️  Please edit .env and add your API keys!"
else
    echo "   ℹ️  .env file already exists"
fi
echo ""

# Check Docker
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker is installed"

    # Start Docker services
    echo "   🚀 Starting Docker services (PostgreSQL, Redis, Qdrant)..."
    docker-compose up -d
    echo "   ✅ Docker services started"

    # Wait for services to be ready
    echo "   ⏳ Waiting for services to be ready..."
    sleep 5
    echo "   ✅ Services should be ready"
else
    echo "   ⚠️  Docker not found. Please install Docker and run: docker-compose up -d"
fi
echo ""

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head
echo "   ✅ Database migrations completed"
echo ""

echo "================================"
echo "✅ Setup completed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env file and add your API keys"
echo "   2. Run: source venv/bin/activate"
echo "   3. Run: uvicorn app.main:app --reload"
echo ""
echo "🌐 The API will be available at: http://localhost:8000"
echo "📚 API docs will be at: http://localhost:8000/docs"
echo ""
echo "Happy coding! 🚀"

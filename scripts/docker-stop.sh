#!/bin/bash

# Chronus AI - Docker Stop Script

echo "🛑 Stopping Chronus AI services..."
docker-compose down

echo ""
echo "✅ All services stopped!"
echo ""
echo "💡 To remove volumes as well, run:"
echo "   docker-compose down -v"

#!/bin/bash

# Chronus AI - Docker Logs Script

echo "📋 Viewing logs for all services..."
echo "   Press Ctrl+C to exit"
echo ""

docker-compose logs -f

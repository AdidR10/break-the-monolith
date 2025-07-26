#!/bin/bash

echo "🛑 Stopping CUET Rickshaw Application..."

# Stop all services
docker-compose down

# Remove volumes (optional - uncomment if you want to reset data)
# docker-compose down -v

echo "✅ CUET Rickshaw has been stopped."

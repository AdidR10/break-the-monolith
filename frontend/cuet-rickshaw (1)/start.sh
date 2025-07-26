#!/bin/bash

# CUET Rickshaw Docker Setup Script

echo "🚀 Starting CUET Rickshaw Application..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
mkdir -p mock-services
mkdir -p ssl

# Build and start the application
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if services are running
echo "🔍 Checking service health..."
docker-compose ps

echo "✅ CUET Rickshaw is now running!"
echo ""
echo "🌐 Application: http://localhost:3000"
echo "🗄️  Database: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo "📊 User Service: http://localhost:8080"
echo "🚗 Ride Service: http://localhost:8081"
echo "📍 Location Service: http://localhost:8082"
echo "💳 Payment Service: http://localhost:8083"
echo "🔔 Notification Service: http://localhost:8084"
echo ""
echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"

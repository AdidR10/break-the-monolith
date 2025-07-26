# 🚀 RickshawX - Smart Campus Mobility Platform

## 🏛️ Microservices Architecture for CUET (Year 2050)

RickshawX is a comprehensive ride-sharing platform built using microservices architecture, designed specifically for CUET's smart campus environment. This project demonstrates modern software architecture principles including service decomposition, API design, inter-service communication, and containerized deployment.

---

## 📋 Table of Contents

- [🏗️ Architecture Overview](#-architecture-overview)
- [🛠️ Technologies Used](#-technologies-used)
- [🚀 Quick Start](#-quick-start)
- [📚 API Documentation](#-api-documentation)
- [🔧 Development Setup](#-development-setup)
- [🐳 Docker Deployment](#-docker-deployment)
- [🔍 Monitoring & Observability](#-monitoring--observability)
- [🧪 Testing](#-testing)
- [📈 Scalability Considerations](#-scalability-considerations)
- [🤝 Contributing](#-contributing)

---

## 🏗️ Architecture Overview

### Microservices Structure

```
🏛️ RickshawX Platform
├── 👤 User Service (Port 8080)
│   ├── User Authentication & Authorization
│   ├── Profile Management (Students & Rickshaw Pullers)
│   └── User Verification & KYC
├── 🚗 Ride Service (Port 8081)
│   ├── Ride Request Management
│   ├── Driver-Rider Matching
│   ├── Trip Lifecycle Management
│   └── Real-time Tracking
├── 📍 Location Service (Port 8082)
│   ├── Campus Location Management
│   ├── Zone-based Routing
│   └── Popular Destinations
├── 💳 Payment Service (Port 8083)
│   ├── Digital Wallet Management
│   ├── Transaction Processing
│   └── Fare Calculation
├── 📱 Notification Service (Port 8084)
│   ├── Real-time Notifications
│   ├── Email & Push Notifications
│   └── Event-driven Messaging
└── 🌐 API Gateway (Port 80)
    ├── Request Routing
    ├── Rate Limiting
    ├── Security Headers
    └── Load Balancing
```

### Infrastructure Components

- **Database**: PostgreSQL (Shared database with service-specific schemas)
- **Message Broker**: RabbitMQ (Event-driven communication)
- **Cache**: Redis (Session management & caching)
- **API Gateway**: Nginx (Reverse proxy & load balancing)
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker & Docker Compose

---

## 🛠️ Technologies Used

### Backend Stack
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and serialization
- **Alembic** - Database migrations
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **RabbitMQ** - Message brokering

### DevOps & Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - API Gateway and reverse proxy
- **Prometheus** - Metrics collection
- **Grafana** - Visualization and monitoring

### Development Tools
- **JWT** - Authentication tokens
- **Bcrypt** - Password hashing
- **Geopy** - Location calculations
- **HTTPX** - Async HTTP client for inter-service communication

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd break-the-monolith
```

### 2. Start All Services
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Verify Services
```bash
# Check service health
curl http://localhost/health

# View API Documentation
open http://localhost/docs

# Access RabbitMQ Management
open http://localhost:15672 (guest/guest)

# Access Grafana Dashboard
open http://localhost:3000 (admin/admin)
```

### 4. Initialize Sample Data
```bash
# Create sample campus locations
curl -X POST "http://localhost/api/v1/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "location_name": "Central Library",
    "zone": "Academic",
    "latitude": 22.4596,
    "longitude": 91.9678,
    "description": "Main library building"
  }'
```

---

## 📚 API Documentation

### 🔑 Authentication Flow

1. **User Registration**
```bash
POST /api/v1/auth/register
{
  "email": "student@cuet.ac.bd",
  "phone": "01712345678",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "STUDENT"
}
```

2. **User Login**
```bash
POST /api/v1/auth/login
{
  "email": "student@cuet.ac.bd",
  "password": "SecurePass123"
}
```

3. **Create Profile** (After Registration)
```bash
# For students
POST /api/v1/student/profile
{
  "student_id": "1804XXX",
  "department": "CSE",
  "batch": "18",
  "year": 4
}

# For rickshaw pullers
POST /api/v1/rickshaw/profile
{
  "rickshaw_number": "CUET-001",
  "license_number": "DL123456"
}
```

### 🚗 Ride Management Flow

1. **Request a Ride** (Student)
```bash
POST /api/v1/requests
{
  "pickup_location": "Central Library",
  "pickup_latitude": 22.4596,
  "pickup_longitude": 91.9678,
  "drop_location": "CSE Building",
  "drop_latitude": 22.4601,
  "drop_longitude": 91.9685,
  "max_wait_time": 15
}
```

2. **View Active Requests** (Driver)
```bash
GET /api/v1/requests/active
```

3. **Make an Offer** (Driver)
```bash
POST /api/v1/offers
{
  "ride_request_id": "uuid",
  "estimated_arrival_time": 5,
  "message": "I'm nearby, can pick you up quickly!"
}
```

4. **Accept Offer** (Student)
```bash
POST /api/v1/offers/{offer_id}/accept
```

5. **Update Ride Status**
```bash
PUT /api/v1/rides/{ride_id}/status
{
  "status": "STARTED"
}
```

### 📍 Location & Fare Services

```bash
# Get campus locations
GET /api/v1/locations?zone=Academic

# Calculate fare
POST /api/v1/fare/calculate
{
  "pickup_latitude": 22.4596,
  "pickup_longitude": 91.9678,
  "drop_latitude": 22.4601,
  "drop_longitude": 91.9685
}

# Find nearby drivers
POST /api/v1/drivers/nearby
{
  "latitude": 22.4596,
  "longitude": 91.9678,
  "radius_km": 2.0
}
```

### 💳 Payment Operations

```bash
# Create wallet
POST /api/v1/wallets
{
  "user_id": "uuid"
}

# Process payment
POST /api/v1/transactions
{
  "ride_id": "uuid",
  "to_user_id": "driver_uuid",
  "amount": 45.50,
  "transaction_type": "RIDE_PAYMENT",
  "description": "Payment for ride"
}
```

---

## 🔧 Development Setup

### Local Development (Without Docker)

1. **Setup Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
# For each service
cd services/user-services
pip install -r requirements.txt

cd ../ride_service
pip install -r requirements.txt
# ... repeat for other services
```

3. **Setup Local Database**
```bash
# Install PostgreSQL locally
# Create database
createdb rickshawx_db

# Set environment variables
export DATABASE_URL=postgresql://postgres:password@localhost/rickshawx_db
export REDIS_HOST=localhost
export RABBITMQ_HOST=localhost
export SECRET_KEY=your-secret-key
```

4. **Run Services Individually**
```bash
# Terminal 1 - User Service
cd services/user-services
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Ride Service
cd services/ride_service
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# ... continue for other services
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add user tables"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🐳 Docker Deployment

### Development Environment
```bash
# Start all services in development mode
docker-compose up --build

# Start specific services
docker-compose up user-service ride-service postgres

# View logs
docker-compose logs -f user-service

# Scale services
docker-compose up --scale ride-service=3
```

### Production Environment
```bash
# Create production docker-compose.prod.yml
# with environment-specific configurations

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Update single service
docker-compose -f docker-compose.prod.yml up -d --no-deps user-service
```

### Service Management
```bash
# Health checks
curl http://localhost/health
curl http://localhost/user/health
curl http://localhost/ride/health

# Service discovery
docker-compose ps

# Resource monitoring
docker stats
```

---

## 🔍 Monitoring & Observability

### Metrics & Monitoring

**Prometheus Metrics (Port 9090)**
- Service health and uptime
- Request rates and latencies
- Database connection pools
- Memory and CPU usage

**Grafana Dashboards (Port 3000)**
- Service Overview Dashboard
- Database Performance
- API Request Analytics
- Business Metrics (rides, users, revenue)

### Logging

**Centralized Logging Strategy**
```python
# Each service includes structured logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
logger.info("Service started", extra={"service": "user-service"})
```

**Log Aggregation** (Production Setup)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Centralized log storage and analysis
- Real-time alerting on errors

### Health Checks

Each service exposes health endpoints:
```bash
GET /health
{
  "status": "healthy",
  "service": "user-service",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 🧪 Testing

### Unit Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx pytest-cov

# Run tests for specific service
cd services/user-services
pytest tests/ -v --cov=app

# Run all tests
pytest tests/ --cov=app --cov-report=html
```

### Integration Testing
```bash
# Test inter-service communication
pytest tests/integration/ -v

# Test with Docker environment
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost
```

### API Testing with Postman

Import the provided Postman collection:
```bash
# Collection includes:
# - Authentication flows
# - CRUD operations for all services
# - End-to-end ride scenarios
# - Error handling cases
```

---

## 📈 Scalability Considerations

### Horizontal Scaling

**Service Scaling**
```yaml
# docker-compose.yml
ride-service:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

**Database Scaling**
- Read replicas for read-heavy operations
- Database sharding by user_id or location
- Connection pooling optimization

**Caching Strategy**
- Redis for session management
- Application-level caching for frequently accessed data
- CDN for static assets

### Performance Optimization

**Database Optimization**
```sql
-- Indexing strategy
CREATE INDEX idx_rides_status ON rides(status);
CREATE INDEX idx_rides_rider_id ON rides(rider_id);
CREATE INDEX idx_rides_driver_id ON rides(driver_id);
CREATE INDEX idx_rides_created_at ON rides(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_rides_status_created ON rides(status, created_at);
```

**API Optimization**
- Pagination for large datasets
- Field selection for API responses
- Async processing for heavy operations
- Request/response compression

### Message Queue Scaling

**RabbitMQ Configuration**
```yaml
# Production settings
rabbitmq:
  environment:
    RABBITMQ_DEFAULT_VHOST: rickshawx
    RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 0.8
  deploy:
    replicas: 3
```

---

## 🔒 Security Considerations

### Authentication & Authorization
- JWT tokens with expiration
- Role-based access control (RBAC)
- API rate limiting
- Input validation and sanitization

### Data Protection
```python
# Sensitive data encryption
from cryptography.fernet import Fernet

# Environment variables for secrets
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
```

### Network Security
```nginx
# nginx.conf security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000";
```

---

## 🚀 Deployment Strategies

### Development Workflow
```bash
# 1. Feature development
git checkout -b feature/user-authentication

# 2. Local testing
docker-compose up --build

# 3. Integration testing
pytest tests/integration/

# 4. Code review and merge
git push origin feature/user-authentication

# 5. CI/CD pipeline
# - Automated testing
# - Docker image building
# - Deployment to staging
```

### Production Deployment

**Container Orchestration** (Kubernetes)
```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: rickshawx/user-service:latest
        ports:
        - containerPort: 8000
```

**CI/CD Pipeline** (GitHub Actions)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build and push Docker images
      run: |
        docker build -t rickshawx/user-service:${{ github.sha }} ./services/user-services
        docker push rickshawx/user-service:${{ github.sha }}
```

---

## 🤝 Contributing

### Development Guidelines

1. **Code Style**
   - Follow PEP 8 for Python code
   - Use type hints for all functions
   - Write comprehensive docstrings

2. **Git Workflow**
   - Feature branches for new development
   - Descriptive commit messages
   - Pull request reviews required

3. **Testing Requirements**
   - Unit tests for all new features
   - Integration tests for API endpoints
   - Minimum 80% code coverage

### Setting Up Development Environment

```bash
# 1. Fork the repository
# 2. Clone your fork
git clone https://github.com/yourusername/break-the-monolith.git

# 3. Create development branch
git checkout -b feature/your-feature-name

# 4. Setup pre-commit hooks
pip install pre-commit
pre-commit install

# 5. Make changes and test
pytest tests/

# 6. Submit pull request
```

---

## 📞 Support & Documentation

### Additional Resources

- **API Documentation**: http://localhost/docs (when running)
- **Architecture Diagrams**: `/docs/architecture/`
- **Database Schema**: `/docs/database/`
- **Deployment Guide**: `/docs/deployment/`

### Troubleshooting

**Common Issues**
```bash
# Service connection issues
docker-compose logs service-name

# Database connection problems
docker-compose exec postgres psql -U postgres -d rickshawx_db

# RabbitMQ queue issues
docker-compose exec rabbitmq rabbitmqctl list_queues

# Redis connection problems
docker-compose exec redis redis-cli ping
```

### Contact Information

- **Project Lead**: IEEE CS CUET
- **Technical Support**: [GitHub Issues](your-repo-url/issues)
- **Documentation**: [Wiki](your-repo-url/wiki)

---

## 📄 License

This project is developed for educational purposes as part of the IEEE CS CUET Microservices Hackathon.

---

**Built with ❤️ by IEEE Computer Society CUET**

*Demonstrating the future of scalable software architecture through practical implementation.* 
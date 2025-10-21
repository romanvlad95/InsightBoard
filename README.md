<div align="center">

# InsightBoard

**Real-time analytics platform with event-driven architecture**

</div>

<div align="center">

[![CI](https://github.com/romanvlad95/InsightBoard/workflows/InsightBoard%20CI/badge.svg)](https://github.com/romanvlad95/InsightBoard/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/react-18.2-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.6-blue.svg)](https://www.typescriptlang.org/)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://github.com/romanvlad95/InsightBoard)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[Live Demo](#) • [Documentation](#getting-started) • [API Docs](http://localhost:8000/docs)

</div>



## Overview

InsightBoard is a production-ready real-time analytics platform that processes and visualizes metrics instantly using an event-driven architecture. Built with modern technologies and best practices, it demonstrates scalable data ingestion, real-time updates via WebSocket, and comprehensive testing.

### Live Preview

![Dashboard Preview](docs/dashboard-preview.png)

*Real-time analytics dashboard with WebSocket updates and interactive charts*



## Key Features

- **Real-time data ingestion** via Apache Kafka streaming
- **Live dashboard updates** through WebSocket + Redis pub/sub
- **JWT authentication** with protected routes
- **Interactive charts** with trend indicators and historical data
- **Full Docker stack** with 6 containerized services
- **91 comprehensive tests** with 85% backend coverage
- **CI/CD pipeline** with GitHub Actions
- **Modern UI** built with React 18 and Tailwind CSS



## Architecture
```mermaid
flowchart LR
    Client[React Client] -->|REST API| Backend[FastAPI]
    Client -->|WebSocket| Backend
    Backend -->|Produce| Kafka[Kafka Stream]
    Kafka -->|Consume| Consumer[Consumer Service]
    Consumer -->|Store| DB[(PostgreSQL)]
    Consumer -->|Publish| Redis[Redis Pub/Sub]
    Redis -->|Broadcast| Backend
    Backend -->|Push Updates| Client
```

### Event-Driven Flow

1. **Ingestion**: Client sends metrics via REST API
2. **Streaming**: FastAPI produces events to Kafka topic
3. **Processing**: Consumer service processes stream and stores in PostgreSQL
4. **Distribution**: Consumer publishes to Redis pub/sub channel
5. **Real-time Updates**: WebSocket broadcasts to all connected clients
6. **Visualization**: React UI updates charts instantly



## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0
- **Streaming**: Apache Kafka
- **Cache**: Redis (pub/sub for WebSocket)
- **Auth**: JWT tokens with passlib

### Frontend
- **Framework**: React 18.2
- **Language**: TypeScript 5.6
- **Build Tool**: Vite 5.0
- **Styling**: Tailwind CSS 3.4
- **Charts**: Recharts 2.10
- **HTTP Client**: Axios

### DevOps & Quality
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Testing**: Pytest (73 tests), Vitest (18 tests)
- **Linting**: Ruff, ESLint
- **Formatting**: Black, Prettier
- **Type Checking**: MyPy
- **Pre-commit Hooks**: Automated quality checks



## Project Structure
```
InsightBoard/
│
├── backend/                    # FastAPI Application
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/  # API route handlers
│   │   │       │   ├── metrics.py
│   │   │       │   └── websocket.py
│   │   │       └── routers/    # Router configuration
│   │   │           ├── auth.py
│   │   │           └── dashboards.py
│   │   ├── core/              # Core configuration
│   │   │   ├── config..py      # Settings management
│   │   │   └── security.py    # JWT utilities
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── dashboard.py
│   │   │   └── metric.py
│   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   └── metric.py
│   │   ├── services/          # Business logic
│   │   │   ├── kafka_producer.py
│   │   │   ├── kafka_consumer.py
│   │   │   ├── redis_service.py
│   │   │   ├── websocket_manager.py
│   │   │   ├── dashboard_service.py
│   │   │   └── metric_service.py
│   │   ├── tests/             # Test suite (73 tests)
│   │   │   ├── unit/          # Unit tests
│   │   │   ├── integration/   # Integration tests
│   │   │   └── conftest.py    # Pytest fixtures
│   │   └── main.py            # Application entry point
│   ├── migrations/            # Alembic migrations
│   ├── pyproject.toml         # Python dependencies
│   └── .env.example           # Environment variables template
│
├── frontend/                   # React Application
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   │   ├── MetricCard.tsx
│   │   │   ├── MetricChart.tsx
│   │   │   └── AddMetricModal.tsx
│   │   ├── contexts/          # React contexts
│   │   │   └── AuthContext.tsx
│   │   ├── pages/             # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Login.tsx
│   │   │   └── Register.tsx
│   │   ├── services/          # API clients
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── test/              # Test suite (18 tests)
│   │   └── App.tsx            # Root component
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docker-compose.yml         # Multi-container orchestration
├── Makefile                   # Development commands
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD pipeline
└── README.md
```



## Getting Started

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience)

### Quick Start

1. **Clone the repository**
```bash
   git clone https://github.com/romanvlad95/InsightBoard.git
   cd InsightBoard
```

2. **Create environment files**
```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configurations
```

3. **Build and start all services**
```bash
   make dev-build
   # OR without make:
   docker compose up --build -d
```

4. **Wait for services to be healthy** (~30 seconds)
```bash
   make health
   # OR:
   curl http://localhost:8000/health
```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### First Steps

1. Register a new user at http://localhost:3000/register
2. Login with your credentials
3. Create a new dashboard
4. Add metrics using the UI or API (see examples below)
5. Watch real-time updates!



## Makefile Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all services |
| `make dev-build` | Build and start all services |
| `make dev-down` | Stop all services |
| `make dev-clean` | Remove all containers, volumes, and networks |
| `make dev-logs` | Follow logs for all services |
| `make backend-shell` | Open bash shell in backend container |
| `make frontend-shell` | Open shell in frontend container |
| `make backend-migrate` | Run database migrations |
| `make test` | Run all tests (backend + frontend) |
| `make test-backend` | Run backend tests |
| `make test-frontend` | Run frontend tests |
| `make coverage` | Generate coverage report |
| `make lint` | Lint all code |
| `make format` | Format all code |
| `make ci` | Run full CI pipeline locally |
| `make health` | Check services health |
| `make status` | Show running services status |
| `make help` | Show all available commands |



## Configuration

### Backend Environment Variables
```env
# Database
DATABASE_URL=postgresql+asyncpg://insightboard:insightboard123@postgres:5432/insightboard

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Redis
REDIS_URL=redis://redis:6379

# JWT Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
PROJECT_NAME=InsightBoard
VERSION=1.0.0
ENVIRONMENT=development
```

Generate a secure secret key:
```bash
openssl rand -hex 32
```

### Frontend Environment Variables
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```



## API Examples

### Authentication

**Register a new user:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
# Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

### Metrics Ingestion

**Send metrics (requires authentication):**
```bash
TOKEN="your-jwt-token-here"

curl -X POST http://localhost:8000/api/v1/metrics/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d \
    "[
      {
        "dashboard_id": 1,
        "name": "cpu_usage",
        "value": 75.5,
        "metric_type": "gauge",
        "tags": {"host": "server-01", "env": "production"}
      },
      {
        "dashboard_id": 1,
        "name": "request_count",
        "value": 1500,
        "metric_type": "counter"
      }
    ]"
```

**Metric Types:**
- `gauge`: Instant values (CPU, memory, temperature)
- `counter`: Cumulative values (requests, errors, events)



## Testing

### Run All Tests
```bash
make test
```

### Backend Tests (73 tests, 85% coverage)
```bash
make test-backend

# With coverage report:
make coverage
```

Test categories:
- **Unit tests**: Services, utilities, models
- **Integration tests**: API endpoints, database operations
- **WebSocket tests**: Real-time communication
- **Kafka tests**: Event streaming

### Frontend Tests (18 tests)
```bash
make test-frontend
```

Test coverage includes:
- Component rendering
- User interactions
- API integration
- WebSocket connections
- Authentication flows



## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

**On every push and PR:**
1. Lint backend (Ruff)
2. Format check (Black)
3. Run backend tests with coverage
4. Lint frontend (ESLint)
5. Run frontend tests
6. Build frontend

**Pre-commit hooks** ensure code quality before commits:
- Trailing whitespace removal
- End-of-file fixes
- YAML validation
- Large file detection
- Python linting and formatting

Install pre-commit hooks:
```bash
cd backend
pre-commit install
```



## Docker Services

The application runs 6 containerized services:

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 3000 | React application (Vite dev server) |
| **Backend** | 8000 | FastAPI application |
| **PostgreSQL** | 5432 | Primary database |
| **Redis** | 6379 | Pub/sub for WebSocket |
| **Kafka** | 9092 | Event streaming platform |
| **Zookeeper** | 2181 | Kafka coordination |

All services include health checks and automatic restart policies.



## Development Stats

| Metric | Value |
|--------|-------|
| **Total Tests** | 91 (73 backend + 18 frontend) |
| **Test Coverage** | 85% (backend) |
| **Lines of Code** | 6,500+ |
| **Technologies** | 15+ |
| **Docker Services** | 6 |
| **API Endpoints** | 12+ |
| **Database Tables** | 3 (users, dashboards, metrics) |



## Roadmap

### v1.1.0 (Planned)
- [ ] Grafana + Prometheus monitoring
- [ ] Advanced chart types (heatmaps, histograms)
- [ ] Data export (CSV, JSON)
- [ ] Alert system with notifications
- [ ] Dashboard templates

### v1.2.0 (Future)
- [ ] Multi-tenancy support
- [ ] RBAC (Role-Based Access Control)
- [ ] Advanced filtering and queries
- [ ] Mobile responsive design improvements



## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



## Acknowledgments

- FastAPI for the excellent async framework
- Apache Kafka for robust event streaming
- React team for the powerful UI library
- All open-source contributors



<div align="center">

**Built with passion using modern technologies**

[⬆ Back to Top](#insightboard)

</div>

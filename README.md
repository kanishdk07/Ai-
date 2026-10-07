# Highway Accident Detection and Emergency Alert System - Backend Module

## Overview
Complete FastAPI-based backend for an AI-powered highway accident detection and emergency alert system with real-time notifications, hospital integration, and admin controls.

## Features
- 🎥 Camera Management (System, Mobile, IP/CCTV cameras)
- 🚨 Real-time Accident Detection & Processing
- 🏥 Automated Hospital Notification with Configurable Intervals
- 🔔 Manual Emergency Contact Mode
- ✅ Hospital Acknowledgment System
- 👨‍💼 Admin Controls & Emergency Stop
- 🔧 Maintenance Mode
- 🔐 JWT Authentication & Role-Based Authorization
- 📡 WebSocket Real-time Updates
- 📊 Audit Logs & System Monitoring
- ✨ Async Task Processing

## Technology Stack
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with PostGIS
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic v2
- **Task Queue**: APScheduler (async)
- **WebSockets**: FastAPI WebSockets
- **Testing**: pytest, pytest-asyncio
- **API Documentation**: OpenAPI 3.1 (auto-generated)

## Project Structure
```
highway-accident-detection-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── database.py             # Database connection and session management
│   ├── dependencies.py         # Shared dependencies (auth, db sessions)
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── incident.py
│   │   ├── hospital.py
│   │   ├── notification.py
│   │   └── audit_log.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── incident.py
│   │   ├── hospital.py
│   │   ├── notification.py
│   │   └── admin.py
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── cameras.py
│   │   │   ├── incidents.py
│   │   │   ├── hospitals.py
│   │   │   ├── notifications.py
│   │   │   ├── admin.py
│   │   │   └── websocket.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── camera_service.py
│   │   ├── incident_service.py
│   │   ├── hospital_service.py
│   │   ├── notification_service.py
│   │   ├── scheduler_service.py
│   │   └── websocket_service.py
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── security.py
│       ├── logging.py
│       └── validators.py
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_cameras.py
│   ├── test_incidents.py
│   ├── test_notifications.py
│   └── test_admin.py
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── docs/                       # API documentation
│   ├── API_SPEC.md
│   └── INTEGRATION.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── alembic.ini
└── README.md
```

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ with PostGIS extension
- pip or poetry

### Setup Steps

1. **Clone and navigate to the project**
```bash
cd highway-accident-detection-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your actual configuration
```

5. **Initialize database**
```bash
# Create PostgreSQL database
createdb highway_accident_detection

# Enable PostGIS extension
psql -d highway_accident_detection -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Run migrations
alembic upgrade head
```

6. **Create admin user (optional)**
```bash
python -m app.scripts.create_admin
```

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Points
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **WebSocket**: ws://localhost:8000/ws/dashboard

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user

### Camera Management
- `GET /api/v1/cameras` - List all cameras
- `POST /api/v1/cameras` - Register new camera
- `GET /api/v1/cameras/{camera_id}` - Get camera details
- `PATCH /api/v1/cameras/{camera_id}` - Update camera
- `POST /api/v1/cameras/{camera_id}/start` - Start monitoring
- `POST /api/v1/cameras/{camera_id}/stop` - Stop monitoring
- `DELETE /api/v1/cameras/{camera_id}` - Remove camera

### Incident Management
- `POST /api/v1/incidents` - Create incident (AI integration endpoint)
- `GET /api/v1/incidents` - List incidents
- `GET /api/v1/incidents/{incident_id}` - Get incident details
- `POST /api/v1/incidents/{incident_id}/acknowledge` - Acknowledge incident
- `POST /api/v1/incidents/{incident_id}/resolve` - Resolve incident
- `POST /api/v1/incidents/{incident_id}/cancel` - Cancel incident

### Hospital Integration
- `GET /api/v1/hospitals/nearby` - Find nearby hospitals

### Notification Management
- `POST /api/v1/notifications/manual` - Send manual notification
- `POST /api/v1/notifications/{incident_id}/stop` - Stop notifications for incident
- `POST /api/v1/admin/notifications/stop-all` - Emergency stop all notifications

### Admin Controls
- `PATCH /api/v1/admin/settings` - Update system settings
- `POST /api/v1/admin/maintenance` - Enable/disable maintenance mode
- `GET /api/v1/admin/audit-logs` - View audit logs
- `GET /api/v1/admin/health` - System health check

### WebSocket
- `WS /ws/dashboard` - Real-time dashboard updates

## Configuration

### Environment Variables
See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `AUTO_NOTIFICATION_ENABLED` - Enable automatic notifications (default: false)
- `NOTIFICATION_INTERVAL_SECONDS` - Repeat interval (default: 60)
- `HOSPITAL_SEARCH_RADIUS_KM` - Hospital search radius (default: 50)

## Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_incidents.py -v
```

## Security Considerations

⚠️ **IMPORTANT SAFETY NOTES**:
1. System is in **TEST MODE** by default
2. Real notifications require explicit configuration
3. Do NOT use production credentials in development
4. Camera stream credentials are encrypted
5. All admin operations are logged
6. Rate limiting is enforced on all endpoints

## Integration Guide

### For AI Module
Send detected accidents to:
```
POST /api/v1/incidents
```

See `docs/INTEGRATION.md` for detailed payload specifications.

### For Frontend Module
- Use JWT tokens for authentication
- Connect to WebSocket for real-time updates
- Follow API specifications in `docs/API_SPEC.md`

### For Database/Alert Module
- Database schema is managed by Alembic migrations
- See `app/models/` for complete schema

## Maintenance Mode

When maintenance mode is enabled:
- All camera monitoring stops
- No new incidents are processed
- Notification scheduling is paused
- Only health checks and admin endpoints remain active

Exit maintenance mode to resume normal operations.

## Monitoring & Logging

- Application logs: `logs/app.log`
- Access logs: `logs/access.log`
- Error logs: `logs/error.log`
- Audit logs: Database table `audit_logs`

## Deployment

### Docker (Optional)
```bash
docker build -t highway-accident-backend .
docker run -p 8000:8000 highway-accident-backend
```

### Systemd Service (Linux)
See deployment guide in `docs/DEPLOYMENT.md`

## Support

For integration questions or issues, refer to:
- `docs/API_SPEC.md` - Complete API specification
- `docs/INTEGRATION.md` - Integration contract for team members
- Interactive API docs at `/docs`

## License

[Your License Here]

## Team Integration Contract

This backend provides stable interfaces for:
- **AI Module**: Incident submission API
- **Frontend Module**: REST APIs and WebSocket
- **Database/Alert Module**: Database models and migrations

Do not modify these interfaces without team coordination.

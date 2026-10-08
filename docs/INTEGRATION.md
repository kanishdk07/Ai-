# Integration Contract

## Highway Accident Detection System - Team Integration Guide

This document defines the stable interfaces and integration contracts between modules.

---

## Overview

The system consists of four main modules:
1. **Backend Module** (This module) - FastAPI REST API and WebSocket server
2. **AI Detection Module** - Computer vision and accident detection
3. **Frontend Module** - Web dashboard and admin interface
4. **Database/Alert Module** - PostgreSQL database and notification providers

---

## 1. AI Module Integration

### AI → Backend: Incident Submission

**Endpoint:** `POST /api/v1/incidents`

**Authentication:** Not required (AI module is trusted)

**Request Schema:**
```typescript
interface IncidentCreate {
  incident_id: string;              // Unique identifier (required)
  camera_external_id?: string;      // Camera ID from AI module
  detected_at: string;              // ISO 8601 timestamp (required)
  accident_detected: boolean;       // Always true for accidents
  severity: "high" | "medium" | "low";  // Required
  confidence_score: number;         // 0.0 to 1.0 (required)
  latitude?: number;                // -90 to 90
  longitude?: number;               // -180 to 180
  location_description?: string;    // Human-readable location
  accident_image_url?: string;      // URL to accident image
  vehicle_count?: number;           // Number of vehicles involved
  vehicle_info?: object;            // Structured vehicle data
  ai_event_data?: object;           // Any additional AI metadata
  idempotency_key?: string;         // For duplicate prevention
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "incident_id": "ACC-2026-10-07-001",
  "status": "detected",
  "created_at": "2026-10-07T04:30:05Z"
}
```

**Error Handling:**
- `400` - Invalid data format
- `409` - Duplicate incident_id
- `503` - System in maintenance mode

**Important Notes:**
- Use `idempotency_key` to safely retry failed requests
- Include `latitude` and `longitude` for automatic hospital notification
- Camera must be registered in backend before first incident submission
- AI module should handle 503 errors by queuing incidents locally

---

## 2. Frontend Module Integration

### Authentication

All frontend requests require JWT authentication:

1. **Login:**
   ```
   POST /api/v1/auth/login
   Body: { "username": "user", "password": "pass" }
   Response: { "access_token": "...", "refresh_token": "..." }
   ```

2. **Use Token:**
   ```
   Authorization: Bearer <access_token>
   ```

3. **Refresh Token:**
   ```
   POST /api/v1/auth/refresh
   Body: { "refresh_token": "..." }
   ```

### Real-time Updates

**WebSocket Connection:**
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/dashboard?token=${accessToken}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // message.type: event type
  // message.data: event data
  // message.timestamp: ISO timestamp
};
```

**Event Types:**
- `incident_created` - New accident detected
- `incident_updated` - Incident status changed
- `incident_acknowledged` - Hospital responded
- `incident_resolved` - Incident closed
- `notification_sent` - Alert sent to hospital
- `notifications_stopped` - Notifications cancelled
- `camera_status_changed` - Camera online/offline
- `maintenance_mode_changed` - System mode changed
- `system_alert` - Critical system message

### Admin Dashboard APIs

**Required Endpoints:**
- `GET /api/v1/incidents` - List incidents with filters
- `GET /api/v1/cameras` - List cameras with status
- `GET /api/v1/hospitals/nearby` - Find hospitals near location
- `POST /api/v1/notifications/manual` - Send manual alert
- `POST /api/v1/incidents/{id}/resolve` - Close incident
- `PATCH /api/v1/admin/settings` - Update system config
- `POST /api/v1/admin/notifications/stop-all` - Emergency stop

---

## 3. Database Module Integration

### Database Schema

The backend uses SQLAlchemy ORM with the following main tables:

**users** - User authentication
**cameras** - Camera registry
**incidents** - Accident events
**hospitals** - Emergency responders
**notifications** - Alert tracking
**audit_logs** - System audit trail

### PostGIS Integration

Location-based queries use PostGIS geography type:
- All coordinates in WGS84 (SRID 4326)
- Distance calculations in meters
- Spatial indexing enabled

### Migrations

Use Alembic for database migrations:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## 4. Notification Provider Integration

### SMS/Email Provider Setup

The backend expects notification providers to implement:

**SMS Provider Interface:**
```python
async def send_sms(
    phone: str,        # E.164 format: +919876543210
    message: str,      # Plain text message
) -> dict:            # Returns provider response
    pass
```

**Email Provider Interface:**
```python
async def send_email(
    to: str,          # Email address
    subject: str,     # Email subject
    body: str,        # Email body (HTML/text)
) -> dict:           # Returns provider response
    pass
```

**Configuration:**
Set in `.env`:
```
SMS_PROVIDER=twilio
SMS_ACCOUNT_SID=your_sid
SMS_AUTH_TOKEN=your_token
SMS_FROM_NUMBER=+1234567890

EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_password
```

---

## 5. Data Flow

### Typical Accident Detection Flow

1. **AI Module** detects accident → `POST /api/v1/incidents`
2. **Backend** creates incident → Broadcasts `incident_created` via WebSocket
3. **Frontend** receives WebSocket event → Updates dashboard
4. **Backend** (if auto-notify enabled):
   - Finds nearby hospitals
   - Schedules repeat notifications
   - Sends SMS/email to hospitals
5. **Hospital** clicks acknowledgment link → `POST /api/v1/incidents/{id}/acknowledge`
6. **Backend** stops notifications → Broadcasts `incident_acknowledged`
7. **Admin** resolves incident → `POST /api/v1/incidents/{id}/resolve`
8. **Backend** closes incident → Broadcasts `incident_resolved`

---

## 6. Configuration Changes

### Coordination Required

Changes to these interfaces require coordination with all teams:

- Incident schema fields (breaking changes)
- Authentication mechanism changes
- WebSocket event structure changes
- Database schema changes affecting multiple modules
- API endpoint URL changes

### Safe to Change

These can be changed without coordination:

- Internal service implementation
- Database query optimization
- Logging and monitoring
- Admin UI features
- Non-breaking field additions (optional fields)

---

## 7. Testing Integration

### AI Module Testing

Test endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "TEST-001",
    "detected_at": "2026-10-07T04:30:00Z",
    "severity": "high",
    "confidence_score": 0.95,
    "latitude": 28.7041,
    "longitude": 77.1025
  }'
```

### Frontend Testing

Test WebSocket:
```javascript
const token = "your_access_token";
const ws = new WebSocket(`ws://localhost:8000/ws/dashboard?token=${token}`);
ws.onopen = () => console.log("Connected");
ws.onmessage = (e) => console.log("Received:", JSON.parse(e.data));
```

### Database Testing

Check connection:
```bash
psql -h localhost -U postgres -d highway_accident_detection -c "SELECT COUNT(*) FROM incidents;"
```

---

## 8. Error Handling Contract

All modules should handle these scenarios:

1. **Backend Unavailable (503)**
   - AI Module: Queue incidents locally, retry with exponential backoff
   - Frontend: Show offline banner, cache user actions

2. **Authentication Failure (401)**
   - Frontend: Redirect to login, clear tokens

3. **Rate Limiting (429)**
   - All modules: Implement exponential backoff

4. **Validation Errors (422)**
   - AI Module: Log validation errors, alert devops
   - Frontend: Show user-friendly error messages

---

## 9. Performance Guidelines

- **AI Module:** Submit incidents within 5 seconds of detection
- **Backend:** Respond to incident creation within 500ms
- **Frontend:** Update UI within 100ms of WebSocket event
- **Notifications:** Send within configured interval (30-300s)

---

## 10. Security Requirements

- All passwords hashed with bcrypt
- JWT tokens expire after 30 minutes (access) / 7 days (refresh)
- Camera stream credentials encrypted in database
- HTTPS required in production
- Rate limiting enabled on all endpoints
- SQL injection protection via parameterized queries
- XSS protection via input sanitization

---

## Support

For integration issues:
- Backend API docs: `http://localhost:8000/docs`
- WebSocket test client: Use the interactive docs
- Integration questions: Contact backend team lead

**Do not modify these interfaces without team coordination.**

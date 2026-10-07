# API Specification

## Highway Accident Detection and Emergency Alert System - Backend API

Version: 1.0.0

Base URL: `http://localhost:8000/api/v1`

---

## Authentication

All endpoints (except `/incidents` POST and `/admin/health`) require JWT authentication.

### Headers
```
Authorization: Bearer <access_token>
```

### Login
**POST** `/api/v1/auth/login`

Request:
```json
{
  "username": "admin",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## Incidents

### Create Incident (AI Integration Endpoint)
**POST** `/api/v1/incidents`

**No authentication required** - Used by AI module

Request:
```json
{
  "incident_id": "ACC-2026-10-07-001",
  "camera_external_id": "CAM-HWY-01",
  "detected_at": "2026-10-07T04:30:00Z",
  "accident_detected": true,
  "severity": "high",
  "confidence_score": 0.92,
  "latitude": 28.7041,
  "longitude": 77.1025,
  "location_description": "NH-48, KM 245",
  "accident_image_url": "https://storage.example.com/accidents/img001.jpg",
  "vehicle_count": 2,
  "vehicle_info": {
    "vehicles": [
      {"type": "car", "color": "red"},
      {"type": "truck", "color": "white"}
    ]
  },
  "ai_event_data": {
    "model_version": "v2.3.1",
    "processing_time_ms": 145
  },
  "idempotency_key": "unique-key-12345"
}
```

Response: `201 Created`
```json
{
  "id": "uuid",
  "incident_id": "ACC-2026-10-07-001",
  "severity": "high",
  "status": "detected",
  "confidence_score": 0.92,
  "detected_at": "2026-10-07T04:30:00Z",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "notification_count": 0,
  "created_at": "2026-10-07T04:30:05Z"
}
```

### List Incidents
**GET** `/api/v1/incidents?skip=0&limit=100&status=active&severity=high`

Response:
```json
{
  "incidents": [...],
  "total": 25,
  "page": 1,
  "page_size": 100
}
```

### Get Incident
**GET** `/api/v1/incidents/{incident_id}`

### Acknowledge Incident
**POST** `/api/v1/incidents/{incident_id}/acknowledge`

Request:
```json
{
  "hospital_id": "uuid",
  "acknowledgment_token": "token-from-notification",
  "notes": "Ambulance dispatched",
  "responder_name": "Dr. Smith"
}
```

Response:
```json
{
  "incident_id": "uuid",
  "status": "acknowledged",
  "acknowledged_at": "2026-10-07T04:35:00Z",
  "hospital_name": "City General Hospital",
  "message": "Incident acknowledged successfully. Emergency response en route."
}
```

### Resolve Incident
**POST** `/api/v1/incidents/{incident_id}/resolve`

Request:
```json
{
  "resolution_notes": "All victims transported to hospital. Scene cleared.",
  "outcome": "successful"
}
```

### Cancel Incident
**POST** `/api/v1/incidents/{incident_id}/cancel`

Request:
```json
{
  "reason": "False positive - routine traffic stop"
}
```

---

## Cameras

### Register Camera
**POST** `/api/v1/cameras`

Request:
```json
{
  "camera_id": "CAM-HWY-01",
  "name": "Highway Cam 1 - NH48 KM245",
  "camera_type": "ip_cctv",
  "location_name": "NH-48 KM 245",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "connection_config": {
    "rtsp_url": "rtsp://camera-server/stream1",
    "username": "admin",
    "password": "encrypted"
  },
  "description": "Main highway monitoring camera"
}
```

### List Cameras
**GET** `/api/v1/cameras?camera_type=ip_cctv&status=monitoring`

### Start Monitoring
**POST** `/api/v1/cameras/{camera_id}/start`

### Stop Monitoring
**POST** `/api/v1/cameras/{camera_id}/stop`

---

## Hospitals

### Register Hospital
**POST** `/api/v1/hospitals`

Request:
```json
{
  "name": "City General Hospital",
  "phone_numbers": ["+919876543210", "+919876543211"],
  "email": "emergency@cityhospital.com",
  "address": "123 Medical Street",
  "city": "Delhi",
  "state": "Delhi",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "has_emergency_dept": true,
  "has_trauma_center": true,
  "has_ambulance": true,
  "is_24_7": true,
  "accepts_sms": true
}
```

### Find Nearby Hospitals
**GET** `/api/v1/hospitals/nearby?latitude=28.7041&longitude=77.1025&radius_km=50&limit=5`

Response:
```json
[
  {
    "id": "uuid",
    "name": "City General Hospital",
    "phone_numbers": ["+919876543210"],
    "address": "123 Medical Street",
    "latitude": 28.7041,
    "longitude": 77.1025,
    "distance_km": 2.5,
    "has_emergency_dept": true,
    "has_ambulance": true,
    "is_available": true
  }
]
```

---

## Notifications

### Send Manual Notification
**POST** `/api/v1/notifications/manual`

Request:
```json
{
  "incident_id": "uuid",
  "recipient_phone": "+919876543210",
  "notification_type": "sms",
  "custom_message": "Emergency: Accident at NH-48 KM 245. Immediate response required."
}
```

### Stop Notifications for Incident
**POST** `/api/v1/notifications/{incident_id}/stop`

Request:
```json
{
  "reason": "Incident resolved",
  "stop_all_for_incident": true
}
```

---

## Admin Controls

### Update System Settings
**PATCH** `/api/v1/admin/settings`

Request:
```json
{
  "auto_notification_enabled": true,
  "notification_interval_seconds": 60,
  "hospital_search_radius_km": 50,
  "max_hospitals_to_notify": 5
}
```

### Maintenance Mode
**POST** `/api/v1/admin/maintenance`

Request:
```json
{
  "enabled": true,
  "reason": "System upgrade",
  "scheduled_end_time": "2026-10-07T06:00:00Z"
}
```

### Emergency Stop All Notifications
**POST** `/api/v1/admin/notifications/stop-all`

Request:
```json
{
  "reason": "Emergency protocol activated",
  "stop_scope": "all"
}
```

### System Health Check
**GET** `/api/v1/admin/health`

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-10-07T04:50:00Z",
  "database_connected": true,
  "scheduler_running": true,
  "active_incidents": 3,
  "pending_notifications": 5,
  "online_cameras": 12,
  "maintenance_mode": false,
  "uptime_seconds": 86400
}
```

---

## WebSocket

### Connect to Dashboard
**WS** `/ws/dashboard?token=<access_token>`

Events received:
```json
{
  "type": "incident_created",
  "data": {
    "incident_id": "ACC-2026-10-07-001",
    "severity": "high",
    "latitude": 28.7041,
    "longitude": 77.1025
  },
  "timestamp": "2026-10-07T04:30:00Z"
}
```

Event types:
- `incident_created`
- `incident_updated`
- `incident_acknowledged`
- `incident_resolved`
- `notification_sent`
- `notifications_stopped`
- `camera_status_changed`
- `maintenance_mode_changed`
- `system_alert`

---

## Error Responses

All endpoints return standardized error responses:

```json
{
  "detail": "Error message description"
}
```

Common status codes:
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Maintenance mode

---

## Rate Limiting

Rate limit: 60 requests per minute per user (configurable)

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1633610400
```

---

## Pagination

List endpoints support pagination:

Query parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100, max: 500)

Response includes:
```json
{
  "items": [...],
  "total": 250,
  "page": 3,
  "page_size": 100
}
```

# SafeWay AI - Highway Accident Detection & Emergency Alert System Frontend

A state-of-the-art, responsive, real-time emergency response command center frontend built with React 18, TypeScript, Tailwind CSS, Leaflet.js, and Recharts.

---

## Executive Overview

The frontend serves as the centralized operator and administrator console for highway surveillance and emergency response. It integrates with the FastAPI backend REST APIs and WebSocket endpoints to provide:
1. **Live Camera Fleet Monitoring** - System USB cameras, field mobile browser streams, and external CCTV RTSP/HLS feeds.
2. **Real-Time AI Accident Detection** - Dynamic vehicle bounding box visualization with YOLO-v9 metadata, speed estimates, tracking IDs, and confidence meters.
3. **Emergency Alert Automation & Hospital Search** - PostGIS spatial radial queries to locate trauma centers and trigger automatic repeat SMS/Call notifications.
4. **Manual Emergency Dispatch** - E.164 phone number validation and immediate custom dispatch to external medical personnel.
5. **Hospital Response & Acknowledgment Tracking** - Real-time WebSocket acknowledgment updates with ambulance dispatch notes, doctor information, and response time metrics.
6. **Critical Safety Controls** - Prominent Emergency Stop (incident & global scope) and Maintenance Mode with safety guards.
7. **Geospatial Accident Map** - Interactive Leaflet map with custom glowing severity markers, radar pulses, camera status pins, and hospital markers.

---

## Technology Stack

- **Framework**: React 18.3 + TypeScript 5.7
- **Build Tool**: Vite 6.1
- **Styling**: Tailwind CSS 3.4 with dark/light themes, glassmorphism, and radar animations
- **Mapping**: Leaflet 1.9 + `@types/leaflet`
- **Charts & Analytics**: Recharts 2.15
- **Icons**: Lucide React
- **HTTP & WebSockets**: Axios with JWT automatic token refresh + Native WebSocket client with exponential backoff & heartbeat ping/pong
- **Testing**: Vitest + React Testing Library + JSDOM

---

## Project Structure

```
frontend/
├── index.html                   # Entry HTML with typography & Leaflet CSS
├── package.json
├── tsconfig.json
├── vite.config.ts               # Proxy configuration to backend (http://localhost:8000)
├── tailwind.config.js           # Emergency theme tokens and animations
├── src/
│   ├── main.tsx                 # React DOM mount point
│   ├── App.tsx                  # Main layout, routing, and provider tree
│   ├── index.css                # Custom scrollbars, glassmorphism, radar pulse CSS
│   ├── types/                   # TypeScript interfaces matching backend models
│   ├── api/
│   │   ├── client.ts            # Axios client with JWT interceptor & refresh
│   │   ├── authApi.ts           # Authentication & login/logout
│   │   ├── cameraApi.ts         # Camera CRUD & monitoring controls
│   │   ├── incidentApi.ts       # Accident lifecycle management
│   │   ├── hospitalApi.ts       # Hospital directory & radial queries
│   │   ├── notificationApi.ts   # Notification history & manual dispatch
│   │   ├── adminApi.ts          # Settings, maintenance, stop-all, & audit logs
│   │   └── mockData.ts          # Realistic highway mock dataset with fallback
│   ├── context/
│   │   ├── AuthContext.tsx      # RBAC session state & quick role switch
│   │   ├── WebSocketContext.tsx # Auto-reconnecting WebSocket link
│   │   ├── IncidentContext.tsx  # Incident state & audio alerts
│   │   ├── SettingsContext.tsx  # Admin rules & maintenance toggle
│   │   └── CameraContext.tsx    # Active camera feeds & WebRTC
│   ├── components/
│   │   ├── common/              # Header, Sidebar, Badges, Modals, Toasts
│   │   ├── dashboard/           # Metrics, Recharts velocity, live feed
│   │   ├── cameras/             # USB webcam, Mobile unit, CCTV players
│   │   ├── monitoring/          # Live bounding box canvas
│   │   ├── incidents/           # Incident table & detail view
│   │   ├── map/                 # Leaflet interactive accident map
│   │   ├── hospitals/           # Hospital directory & manual contact form
│   │   ├── notifications/       # Repeat cycle queue & stop messaging
│   │   └── admin/               # Settings, maintenance, health, audit logs
│   └── tests/                   # Vitest unit & integration test suites
```

---

## Setup & Running Instructions

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```
The application will launch on `http://localhost:5173` with automatic API and WebSocket proxying to `http://localhost:8000`.

### 3. Run Test Suite
```bash
npm run test
```

### 4. Build for Production
```bash
npm run build
```

---

## User Roles & Credentials

For instant evaluation and testing, the application includes a **Quick Role Switcher** in the top-right user profile dropdown:

| Role | Default Username | Permissions |
|---|---|---|
| **Admin** | `admin` | Full system control: System settings, repeat intervals, maintenance mode, global emergency stop, camera & hospital management, incident resolution |
| **Operator** | `operator` | Live camera monitoring, USB & mobile streaming, incident verification, manual SMS dispatch, hospital acknowledgment tracking, incident resolution |
| **Viewer** | `viewer` | Read-only inspection of camera streams, incident tables, and map visualization |

---

## Safety & Security Safeguards

- **RTSP Credential Masking**: Raw CCTV passwords are encrypted on the backend and never exposed in frontend responses.
- **Maintenance Mode Guard**: Blocks live incident submissions and pauses repeat notification cycles, preserving historical logs.
- **Accident Verification Guard**: Distinguishes unconfirmed AI detections from confirmed emergencies with clear "Requires Verification" labels.
- **Idempotent Actions**: Disables duplicate button clicks and displays confirmed backend states.

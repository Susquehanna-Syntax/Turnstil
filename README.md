# Turnstil — Event Management System

QR-based event registration, check-in, and contact sharing platform.  
Built by **Susquehanna Syntax**.

## Quick Start (SQLite — No Docker)

```bash
# Clone and enter directory
cd turnstil

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_demo

# Or just create an admin user
python manage.py seed_admin
python manage.py seed_admin --username myadmin --password secret123 --email me@example.com

# Run server
python manage.py runserver
```

Open http://localhost:8000

## Quick Start (Docker + PostgreSQL)

```bash
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

Open http://localhost:8000

## Demo Accounts

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin1234` | Admin (full access) |
| `organizer` | `organize1234` | Organizer (create events, assign staff) |
| `staff` | `staff1234` | Staff (scan check-ins) |
| `alice` through `eve` | `attendee1234` | Attendees |

## Project Structure

```
turnstil/
├── config/          # Django project settings
├── core/            # Main app (models, views, API, templates)
│   ├── models.py        # User, Person, Event, Ticket, ScanLog
│   ├── views.py         # REST API views
│   ├── web_views.py     # Server-rendered page views
│   ├── serializers.py   # DRF serializers
│   ├── api_urls.py      # /api/* routes
│   └── urls.py          # Web page routes
├── templates/       # Django templates (custom CSS)
│   ├── scanner/         # QR scanner interface
│   ├── admin_portal/    # Dashboard, event management
│   ├── public/          # Home, profile, QR display
│   └── registration/    # Login, register
└── static/          # CSS, JS, images
```

## Key Features

- **Persistent QR Identity** — One UUID per person, works across all events
- **Two Scanner Modes** — Attendance (check-in) and Discovery (networking)
- **Visibility Controls** — Users choose which contact fields to share
- **Full Audit Trail** — Every scan attempt logged with timestamps
- **Role-Based Access** — Attendee → Staff → Organizer → Admin
- **REST API + JWT** — Full API alongside server-rendered pages

## API Endpoints

All responses follow the envelope format:
```json
{ "status": "success" | "error", "data": { ... } }
```

Authenticated endpoints require a JWT bearer token:
```
Authorization: Bearer <access_token>
```

---

### Auth

#### `POST /api/auth/register`
Create a new account. Automatically creates a Person record and returns JWT tokens.

**Auth:** None

**Request body:**
```json
{
  "username": "jsmith",
  "email": "j@example.com",
  "password": "mypassword",
  "name": "Jane Smith",
  "organization": "Acme Corp"
}
```

**Response `201`:**
```json
{
  "status": "success",
  "data": {
    "user": { "id": 1, "username": "jsmith", "email": "...", "role": "attendee", "person_uuid": "...", "person_name": "Jane Smith" },
    "person_uuid": "<uuid>",
    "tokens": { "access": "<jwt>", "refresh": "<jwt>" }
  }
}
```

---

#### `POST /api/auth/login`
Get JWT tokens for an existing account.

**Auth:** None

**Request body:**
```json
{ "username": "jsmith", "password": "mypassword" }
```

**Response `200`:**
```json
{ "access": "<jwt>", "refresh": "<jwt>" }
```

---

#### `POST /api/auth/refresh`
Exchange a refresh token for a new access token.

**Auth:** None

**Request body:**
```json
{ "refresh": "<refresh_token>" }
```

**Response `200`:**
```json
{ "access": "<new_jwt>" }
```

---

#### `GET /api/auth/me`
Return the current user's profile.

**Auth:** JWT (any role)

**Response `200`:**
```json
{
  "status": "success",
  "data": { "id": 1, "username": "jsmith", "email": "...", "role": "attendee", "person_uuid": "<uuid>", "person_name": "Jane Smith" }
}
```

---

### People

#### `GET /api/people/{uuid}/contact`
Return a person's contact card. The owner sees all fields; others see only fields the person has marked visible.

**Auth:** JWT (any role)

**Response `200`:**
```json
{
  "status": "success",
  "data": { "name": "Jane Smith", "email": "j@example.com", "organization": "Acme", "phone": "...", "links": { ... } }
}
```

---

#### `PATCH /api/people/{uuid}/contact`
Update contact fields. Owner only.

**Auth:** JWT (owner)

**Request body** (all fields optional):
```json
{
  "name": "Jane Smith",
  "email": "new@example.com",
  "organization": "New Org",
  "phone": "555-1234",
  "links": { "linkedin": "https://..." },
  "visibility": { "email": true, "phone": false }
}
```

**Response `200`:** Full updated person object.

---

#### `GET /api/people/{uuid}/qr`
Return the person's QR code as a PNG image. Owner or admin only.

**Auth:** JWT (owner or admin)

**Response `200`:** `Content-Type: image/png`

---

#### `GET /api/people/search/?q={query}`
Search attendees by name. Returns up to 10 matches.

**Auth:** JWT (staff or above)

**Response `200`:**
```json
{
  "status": "success",
  "data": [
    { "id": "<uuid>", "name": "Jane Smith", "organization": "Acme" }
  ]
}
```

---

### Events

#### `GET /api/events`
List all events.

**Auth:** JWT (any role)

**Response `200`:** Array of event objects with `registered_count`, `checkin_count`, `is_full`.

---

#### `POST /api/events`
Create a new event. Creator is automatically added as staff.

**Auth:** JWT (organizer or above)

**Request body:**
```json
{
  "name": "Tech Meetup",
  "description": "...",
  "location": "Room 101",
  "start_time": "2026-04-01T18:00:00Z",
  "end_time": "2026-04-01T21:00:00Z",
  "capacity": 100
}
```

**Response `201`:** Full event object.

---

#### `GET /api/events/{uuid}`
Get a single event by UUID.

**Auth:** JWT (any role)

**Response `200`:** Full event object.

---

#### `POST /api/events/{uuid}/register`
Register the currently authenticated user for an event. Returns `409` if already registered or event is full. Returns `403` if registration window is closed.

**Auth:** JWT (any role)

**Request body:** None

**Response `201`:**
```json
{
  "status": "success",
  "data": { "id": "<uuid>", "person": "<uuid>", "event": "<uuid>", "status": "issued", "issued_at": "..." }
}
```

**Error codes:**
| Code | HTTP | Meaning |
|------|------|---------|
| `REGISTRATION_CLOSED` | 403 | Outside reg window |
| `EVENT_FULL` | 409 | At capacity |
| `ALREADY_REGISTERED` | 409 | Duplicate registration |

---

#### `GET /api/events/{uuid}/staff`
List staff assigned to the event.

**Auth:** JWT (organizer or above)

**Response `200`:** Array of user objects.

---

#### `POST /api/events/{uuid}/staff`
Assign a user as staff for the event. Only the event creator or an admin can do this.

**Auth:** JWT (organizer or above, and must own the event)

**Request body:**
```json
{ "user_id": 42 }
```

**Response `200`:**
```json
{ "status": "success", "message": "jsmith assigned as staff." }
```

---

#### `DELETE /api/events/{uuid}/staff`
Remove a user from the event's staff list.

**Auth:** JWT (organizer or above, and must own the event)

**Request body:**
```json
{ "user_id": 42 }
```

---

#### `GET /api/events/{uuid}/dashboard`
Live event stats and the 20 most recent scan log entries.

**Auth:** JWT (event staff or above)

**Response `200`:**
```json
{
  "status": "success",
  "data": {
    "event": { ... },
    "stats": { "registered": 80, "checked_in": 45, "capacity": 100, "is_full": false },
    "recent_scans": [ ... ]
  }
}
```

---

### Check-in

#### `POST /api/checkin`
Process a QR scan for attendance check-in. Every attempt is logged regardless of outcome.

**Auth:** JWT (must be staff for the specified event)

**Request body:**
```json
{
  "person_uuid": "<person-uuid>",
  "event_uuid": "<event-uuid>"
}
```

**Response `200` (success):**
```json
{
  "status": "success",
  "data": { "person_name": "Jane Smith", "checked_in_at": "2026-04-01T18:32:00Z", "event_name": "Tech Meetup" }
}
```

**Error codes:**
| Code | HTTP | Meaning |
|------|------|---------|
| `INVALID` | 404 | Person or event UUID not found |
| `UNAUTHORIZED` | 403 | Scanner is not staff for this event |
| `NOT_REGISTERED` | 404 | Person has no ticket (walk-ins disabled) |
| `EVENT_FULL` | 409 | Walk-in attempted but event is at capacity |
| `DUPLICATE_CHECKIN` | 409 | Person already checked in |
| `TICKET_CANCELED` | 409 | Ticket was canceled |

---

### Logs

#### `GET /api/logs`
Query the full scan audit log. Supports optional filtering.

**Auth:** JWT (admin only)

**Query params:**
| Param | Description |
|-------|-------------|
| `event` | Filter by event UUID |
| `result` | Filter by result: `success`, `duplicate`, `not_registered`, `invalid` |

**Example:**
```
GET /api/logs?event=<uuid>&result=success
```

**Response `200`:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "event": "<uuid>",
      "person": "<uuid>",
      "person_name": "Jane Smith",
      "actor": 3,
      "actor_name": "staffuser",
      "result": "success",
      "scanned_value": "",
      "metadata": {},
      "timestamp": "2026-04-01T18:32:00Z"
    }
  ]
}
```

## Scanner (Mobile)

The scanner at `/scanner/` uses the html5-qrcode library for camera-based scanning. For mobile testing over HTTPS (required for camera), use ngrok:

```bash
ngrok http 8000
```

Then add the ngrok domain to `ALLOWED_HOSTS` in settings.

## Tech Stack

Django 5 · Django REST Framework · SimpleJWT · PostgreSQL/SQLite · html5-qrcode · Docker
# Turnstil

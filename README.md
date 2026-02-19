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
├── templates/       # Django templates (Pico CSS)
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

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/auth/register` | None | Create account + get QR |
| POST | `/api/auth/login` | None | Get JWT tokens |
| GET | `/api/auth/me` | JWT | Current user info |
| GET | `/api/people/{uuid}/contact` | JWT | Contact card (visibility-aware) |
| PATCH | `/api/people/{uuid}/contact` | Owner | Update profile |
| GET | `/api/people/{uuid}/qr` | Owner | QR code image (PNG) |
| GET/POST | `/api/events` | JWT/Org | List or create events |
| POST | `/api/events/{uuid}/register` | JWT | Register for event |
| POST | `/api/checkin` | Staff | Process check-in scan |
| GET | `/api/events/{uuid}/dashboard` | Staff | Live event stats |
| GET | `/api/logs` | Admin | Audit log query |

## Scanner (Mobile)

The scanner at `/scanner/` uses the html5-qrcode library for camera-based scanning. For mobile testing over HTTPS (required for camera), use ngrok:

```bash
ngrok http 8000
```

Then add the ngrok domain to `ALLOWED_HOSTS` in settings.

## Tech Stack

Django 5 · Django REST Framework · SimpleJWT · PostgreSQL/SQLite · Pico CSS · html5-qrcode · Docker
# Turnstil

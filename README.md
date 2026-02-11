# IT Operations Dashboard

> A full-stack IT operations monitoring dashboard built with FastAPI, PostgreSQL, and vanilla JavaScript. Demonstrates both Systemintegration and Anwendungsentwicklung skills.

**Live Demo:** Deployed on Render.com (free tier)

## Features

- **Real-time Service Monitoring** — HTTP, Ping, and TCP health checks with 60-second intervals
- **Ticket Management** — Full CRUD with priority tracking, status workflow, and filtering
- **Network Tools** — DNS lookup, IP geolocation, port scanning, and reverse DNS
- **Knowledge Base** — Markdown articles with full-text search and category filtering
- **Live Dashboard** — WebSocket-powered event feed, Chart.js visualizations, KPI cards
- **System Logs** — Filterable log viewer with auto-refresh and level/source filtering
- **Mobile Responsive** — Works on desktop, tablet, and phone

## Tech Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Backend    | Python 3.11, FastAPI, SQLAlchemy 2.0    |
| Database   | PostgreSQL (async via asyncpg)          |
| Frontend   | HTML5, Tailwind CSS, Chart.js, Vanilla JS |
| Real-time  | WebSockets                              |
| Deployment | Render.com (Infrastructure as Code)     |

## Architecture

```
Browser ──── HTTP/WS ────> FastAPI ──── async ────> PostgreSQL
   │                          │
   │  Tailwind CSS            │  Background Tasks
   │  Chart.js                │  Health Checker (60s loop)
   │  WebSocket Client        │  WebSocket Broadcast
   │                          │
   └── Vanilla JavaScript     └── Jinja2 Templates
```

## API Endpoints

### Services
| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| GET    | `/api/services`               | List all services        |
| POST   | `/api/services`               | Add monitored service    |
| GET    | `/api/services/{id}`          | Get service details      |
| PUT    | `/api/services/{id}`          | Update service config    |
| DELETE | `/api/services/{id}`          | Remove service           |
| POST   | `/api/services/{id}/check`    | Trigger manual check     |
| GET    | `/api/services/stats`         | Aggregate statistics     |

### Tickets
| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| GET    | `/api/tickets`                | List tickets (filterable)|
| POST   | `/api/tickets`                | Create ticket            |
| GET    | `/api/tickets/{id}`           | Get ticket details       |
| PUT    | `/api/tickets/{id}`           | Update ticket            |
| DELETE | `/api/tickets/{id}`           | Delete ticket            |
| GET    | `/api/tickets/stats`          | Ticket statistics        |

### Network Tools
| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| POST   | `/api/network/dns`            | DNS lookup               |
| POST   | `/api/network/geoip`          | IP geolocation           |
| POST   | `/api/network/portscan`       | Port scanner             |
| POST   | `/api/network/reverse-dns`    | Reverse DNS              |

### Knowledge Base
| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| GET    | `/api/knowledge`              | List articles (search)   |
| POST   | `/api/knowledge`              | Create article           |
| GET    | `/api/knowledge/{id}`         | Get article              |
| PUT    | `/api/knowledge/{id}`         | Update article           |
| DELETE | `/api/knowledge/{id}`         | Delete article           |

### System
| Method | Endpoint       | Description              |
|--------|----------------|--------------------------|
| GET    | `/health`      | Health check endpoint    |
| WS     | `/ws/live-feed`| Real-time event stream   |
| GET    | `/docs`        | Swagger API documentation|

## Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/it-ops-dashboard.git
cd it-ops-dashboard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the server (uses SQLite locally by default)
uvicorn app.main:app --reload

# Open in browser
# http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Deployment (Render.com)

This project includes a `render.yaml` Blueprint for one-click deployment:

1. Push this repository to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New" > "Blueprint" and connect your repository
4. Render will auto-create the PostgreSQL database and web service

**Note:** Free tier services spin down after 15 minutes of inactivity. First request after idle will take ~30 seconds.

## Project Structure

```
app/
  main.py              # FastAPI entry point with lifespan events
  config.py            # Environment configuration
  database.py          # SQLAlchemy async engine and session
  models/              # SQLAlchemy ORM models
  routers/             # API endpoints and page routes
  services/            # Business logic (health checker, network tools)
  static/              # CSS, JavaScript, images
  templates/           # Jinja2 HTML templates
tests/                 # Test files
seed.py                # Database seed script
render.yaml            # Render.com deployment blueprint
```

## License

MIT

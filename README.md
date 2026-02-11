# IT Operations Dashboard

> A full-stack IT operations monitoring dashboard built with FastAPI, PostgreSQL, and vanilla JS.

## Tech Stack

| Layer      | Technology                         |
|------------|------------------------------------|
| Backend    | Python 3.11, FastAPI, SQLAlchemy   |
| Database   | PostgreSQL (Render managed)        |
| Frontend   | HTML5, Tailwind CSS, Chart.js      |
| Real-time  | WebSockets                         |
| Deployment | Render.com (auto-deploy from Git)  |

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

# Copy environment file and configure
cp .env.example .env

# Run the server
uvicorn app.main:app --reload
```

## License

MIT

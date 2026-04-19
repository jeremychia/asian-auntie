# Engineering Setup

Developer reference for running, configuring, and deploying Asian Auntie.

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Web framework | Flask 3.x | Python, one process, no build step |
| Web auth | Flask-Login 0.6.x + Flask-Bcrypt 1.0.x | Session cookies for browser |
| API auth | flask-jwt-extended 4.x | JWT tokens for mobile/API clients |
| API security | flask-limiter 3.x + flask-cors 4.x | Rate limiting + CORS |
| Input validation | marshmallow 3.x | API routes only (WTForms for web) |
| Database ORM | SQLAlchemy 2.x + Flask-SQLAlchemy | Works with SQLite and PostgreSQL |
| Migrations | Alembic (via Flask-Migrate) | Schema versioning |
| DB (local) | SQLite | Zero config, single file |
| DB (cloud) | PostgreSQL | Render free tier |
| Frontend | HTMX 2.x + Pico CSS 2.x | Both via CDN, no build step |
| Logging | structlog 24.x | JSON in prod, pretty in dev |
| Image processing | Pillow | Resize before Vision API calls |
| AI (future) | openai >= 1.x | GPT-4o Vision for recognition |
| Production server | Gunicorn | Render deploy |

---

## Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) — fast Python package manager (replaces pip + venv)

Install `uv` (one-time, system-wide):
```bash
brew install uv          # macOS
# or: curl -LsSf https://astral.sh/uv/install.sh | sh
```

That's it. No Node.js, no Docker, no pip management.

---

## One-Time Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd asian-auntie

# 2. Install dependencies (uv creates the venv automatically)
uv sync

# 3. Set up environment variables
cp .env.example .env
# Open .env and fill in FLASK_SECRET_KEY and JWT_SECRET_KEY (see below)

# 4. Initialise the database
uv run flask --app wsgi db upgrade
```

Or just run `make setup` which does steps 2–4 in one command.

---

## Environment Variables

All variables live in `.env` (gitignored). See `.env.example` for the template.

| Variable | Required | Description |
|---|---|---|
| `FLASK_SECRET_KEY` | Yes | Signs session cookies. Must be random and secret. |
| `JWT_SECRET_KEY` | Yes | Signs JWT tokens. Must be different from `FLASK_SECRET_KEY`. |
| `DATABASE_URL` | No | Defaults to `sqlite:///app.db` for local dev. Set to Postgres URL in prod. |
| `OPENAI_API_KEY` | No | Leave blank to use stub mode (app works without it). |
| `LOG_LEVEL` | No | Defaults to `INFO`. Set to `DEBUG` for verbose output. |
| `FLASK_ENV` | No | `development` locally, `production` on Render. |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins. Defaults to `http://localhost:5000`. |

### Generating secret keys

```bash
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

Run this twice — once for `FLASK_SECRET_KEY`, once for `JWT_SECRET_KEY`. Use different values.

---

## Running Locally

```bash
make dev
# expands to: uv run flask --app wsgi run --host=0.0.0.0 --port=5000 --debug
```

- **Laptop**: open `http://localhost:8080`
- **Phone** (same WiFi): find your Mac's local IP, then open `http://<ip>:8080`

> **Note**: Port 5000 is reserved by macOS AirPlay Receiver. The app runs on port 8080 instead.

### Finding your local IP

```bash
ipconfig getifaddr en0
# Example output: 192.168.1.42
# Then open http://192.168.1.42:5000 on your phone
```

> **macOS firewall note**: if the phone can't connect, go to System Settings → Network → Firewall and allow incoming connections for Python, or temporarily disable the firewall for testing.

---

## Adding the App to Your Phone's Home Screen

The app ships with a `manifest.json` and viewport meta tag, so it behaves like a native app when bookmarked.

**iOS (Safari)**:
1. Open `http://<ip>:5000` in Safari
2. Tap the Share button → "Add to Home Screen"
3. Tap "Add" — the app icon appears on your home screen

**Android (Chrome)**:
1. Open `http://<ip>:5000` in Chrome
2. Tap the menu (⋮) → "Add to Home screen"
3. Tap "Add"

---

## Database Commands

```bash
# Apply all pending migrations (run this after pulling changes)
flask db upgrade

# Create a new migration after changing models.py
flask db migrate -m "describe what changed"

# Downgrade one step
flask db downgrade
```

The SQLite database file is `instance/app.db` (gitignored). Delete it and re-run `flask db upgrade` to start fresh locally.

---

## Stub Mode (no API key)

If `OPENAI_API_KEY` is not set, the recognition service returns a zero-confidence result, which routes the user to the manual entry form. The full app works without an API key — you just won't get image recognition.

To test recognition locally, add your key to `.env`:
```
OPENAI_API_KEY=sk-...
```

---

## Cloud Deploy (Render)

1. Push the repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo
3. Set the following in Render's environment variables dashboard:
   - `FLASK_SECRET_KEY` — generate a fresh value
   - `JWT_SECRET_KEY` — generate a fresh value (different from above)
   - `DATABASE_URL` — Render provides this automatically if you add a PostgreSQL database
   - `OPENAI_API_KEY` — if you want recognition enabled
   - `FLASK_ENV=production`
   - `ALLOWED_ORIGINS=https://your-app.onrender.com`
4. Build command: `pip install uv && uv sync && uv run flask --app wsgi db upgrade`
5. Start command: `uv run gunicorn wsgi:app`

Render provides HTTPS automatically. The app will be accessible at `https://your-app.onrender.com`.

> **Free tier note**: Render's free tier spins the server down after 15 minutes of inactivity. The first request after idle takes ~30 seconds to wake up. This is fine for a prototype — warn testers to expect a slow first load.

---

## Project Structure

```
asian-auntie/
├── app/
│   ├── __init__.py            # create_app() factory
│   ├── extensions.py          # db, login_manager, bcrypt, jwt, limiter, cors
│   ├── models.py              # User, Item, RefreshToken
│   ├── logging_config.py      # structlog setup
│   ├── auth/                  # Web auth routes (/login, /logout, /register)
│   ├── api/                   # JSON API routes (/api/v1/...)
│   ├── perishables/           # Web perishables routes (/dashboard, /items/...)
│   └── recognition/           # Image recognition service (OpenAI Vision)
├── templates/                 # Jinja2 HTML templates
├── static/                    # manifest.json, CSS, icons
├── migrations/                # Alembic migration files
├── uploads/                   # Item photos — gitignored
├── instance/                  # SQLite db file — gitignored
├── config.py                  # Dev/Prod config classes
├── wsgi.py                    # Gunicorn entry point
├── requirements.txt
├── Makefile
└── .env.example
```

---

## Auth Architecture

Two parallel auth systems share one `users` table:

| | Web (browser) | API (mobile/API clients) |
|---|---|---|
| Mechanism | Session cookie (Flask-Login) | JWT Bearer token (flask-jwt-extended) |
| Login endpoint | `POST /login` | `POST /api/v1/auth/login` |
| Token lifetime | Browser session + remember_me | Access: 15 min / Refresh: 30 days |
| Logout | Clears cookie | Revokes refresh token in DB |
| Route guard | `@login_required` | `@jwt_required()` |

See [docs/auth/flows.yaml](../auth/flows.yaml) for full flow details including edge cases and decision points.

---

## Logging

Logs are written to stdout via `structlog`.

- **Dev**: human-readable coloured output
- **Prod**: JSON (one object per line — Render captures this automatically)

Every log line includes: `event`, `level`, `timestamp`, and relevant context (`user_id`, `path`, `status`, etc.).

Set `LOG_LEVEL=DEBUG` in `.env` to see all log output including DB queries.

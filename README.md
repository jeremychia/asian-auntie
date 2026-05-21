# asian-auntie

Asian pantry management for cooking inspiration and perishables tracking.

## Overview

`asian-auntie` is a Flask application designed to help users manage pantry perishables, reduce waste, and discover cooking inspiration.

## Docs and Guides

For project documentation, start with the docs index and feature guides:

- [Documentation Index](docs/INDEX.md)
- [Project Quick Start](docs/QUICK-START.md)
- [Documentation Strategy](docs/DOCUMENTATION-STRATEGY.md)
- [Design FAQ](DESIGN-FAQ.md)

Feature-specific documentation:

- [Manage Perishables](docs/manage-perishables/README.md)
- [Recommend Recipe](docs/recommend-recipe/README.md)
- [Trade Perishables](docs/trade-perishables/README.md)

## Getting Started

1. Create and activate a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies and initialize the app:

```bash
make setup
```

3. Start the development server:

```bash
make dev
```

4. Open the app:

```text
http://localhost:8080
```

## Image Recognition

The app can identify pantry items from photos. Three providers are supported — the first one configured wins:

| Priority | Provider           | When to use                          | Setup                                                   |
| -------- | ------------------ | ------------------------------------ | ------------------------------------------------------- |
| 1        | **Ollama** (local) | Local development — free, no API key | See below                                               |
| 2        | **Groq**           | Production — free tier               | Set `GROQ_API_KEY`                                      |
| 3        | **OpenAI**         | Fallback — best accuracy             | Set `OPENAI_API_KEY`                                    |
| —        | Stub               | No provider configured               | Returns zero-confidence result, manual entry form shown |

### Local development with Ollama

1. Install Ollama:

   ```bash
   brew install ollama
   ```

2. Pull the vision model (~7 GB):

   ```bash
   ollama pull llama3.2-vision
   ```

3. Start Ollama (or add it to login items with `brew services start ollama`):

   ```bash
   ollama serve
   ```

4. Add to your `.env`:
   ```
   OLLAMA_BASE_URL=http://localhost:11434
   ```

### Production (Render)

Set `GROQ_API_KEY` in the Render dashboard. Get a free key at [console.groq.com](https://console.groq.com). No other recognition config is needed.

## Configuration

Copy the environment template and edit values as needed:

```bash
cp -n .env.example .env
```

Key environment variables:

| Variable                         | Required in prod | Description                                                                                                         |
| -------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------- |
| `FLASK_SECRET_KEY`               | Yes              | Flask session signing key                                                                                           |
| `JWT_SECRET_KEY`                 | Yes              | JWT signing key (different from above)                                                                              |
| `DATABASE_URL`                   | Yes              | Postgres connection string                                                                                          |
| `VAPID_PRIVATE_KEY`              | Yes              | VAPID private key for web push notifications                                                                        |
| `VAPID_PUBLIC_KEY`               | Yes              | VAPID public key for web push notifications                                                                         |
| `VAPID_CLAIMS_EMAIL`             | No               | Contact email sent with push requests (default: `admin@asian-auntie.app`)                                           |
| `GROQ_API_KEY`                   | Recommended      | Groq API key for item recognition                                                                                   |
| `OPENAI_API_KEY`                 | Fallback         | OpenAI key if Groq not set                                                                                          |
| `OLLAMA_BASE_URL`                | Local dev        | Ollama server URL, e.g. `http://localhost:11434`                                                                    |
| `GCS_BUCKET_NAME`                | Yes              | GCS bucket for photo uploads (e.g. `asian-auntie-items-prod`)                                                       |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes              | Path to service account key file (local: `gcp-service-account.json`, prod: `/etc/secrets/gcp-service-account.json`) |
| `LOG_LEVEL`                      | No               | `DEBUG`, `INFO`, `WARNING`, or `ERROR` (default: `INFO`)                                                            |
| `FLASK_ENV`                      | No               | `development` or `production`                                                                                       |
| `ALLOWED_ORIGINS`                | Yes              | Comma-separated CORS origins                                                                                        |

> **Production startup guard** — when `FLASK_ENV=production`, the app will refuse to start if any of `FLASK_SECRET_KEY`, `JWT_SECRET_KEY`, `VAPID_PRIVATE_KEY`, or `VAPID_PUBLIC_KEY` are missing. In development, `FLASK_SECRET_KEY` and `JWT_SECRET_KEY` fall back to a random value per restart (sessions won't survive restarts, which is fine locally).

## Development Commands

- `make dev` — run the development server
- `make setup` — install dependencies, install Git hooks, and run migrations
- `make migrate msg="Your message"` — create and apply a new migration

## Data Storage

### Database

User data is stored in Postgres in production (set via `DATABASE_URL`). SQLite is used locally by default.

Key tables:

| Table                | What's stored                                                                            |
| -------------------- | ---------------------------------------------------------------------------------------- |
| `users`              | Credentials, onboarding preferences (location, cuisines, household size), consent record |
| `items`              | Pantry items — name, type, expiry date, soft-delete metadata                             |
| `item_photos`        | URLs of uploaded photos (GCS in production, local `uploads/` in dev)                     |
| `recipe_engagements` | Per-user recipe feedback (made it, not for me, skip reason)                              |
| `recognition_cache`  | Cached OCR results keyed by image hash                                                   |
| `refresh_tokens`     | JWT refresh tokens with revocation support                                               |

### Photo storage

In production, photos are stored in Google Cloud Storage. In local development (when `GCS_BUCKET_NAME` is not set), photos are written to the `uploads/` folder.

The `item_photos` table stores either a GCS public URL or a local filename — the app handles both transparently.

## Deploying to Render

The repo includes a `render.yaml` for one-click deploys. This section walks through the full setup.

### Prerequisites

- A [Render](https://render.com) account
- A [Google Cloud](https://console.cloud.google.com) project with a GCS bucket created
- A [Neon](https://neon.tech) project for the Postgres database

### 1. Create GCS buckets and a service account

Create two buckets — one per environment:

| Bucket                    | Used by                                                    |
| ------------------------- | ---------------------------------------------------------- |
| `asian-auntie-items-prod` | Render production                                          |
| `asian-auntie-items-dev`  | Local dev (optional, only if you want to test GCS locally) |

Photos are stored under a `users/{user_id}/` prefix inside each bucket, so each user's files are grouped together.

For each bucket:

1. Set access control to **uniform**.
2. Grant `allUsers` the **Storage Object Viewer** role so photos are publicly readable.

Then create a single service account with the **Storage Object Admin** role on both buckets and generate a JSON key.

### 2. Create a Postgres database on Neon

Create a project at [neon.tech](https://neon.tech). Copy the **pooled connection string** (the one with `-pooler` in the hostname) — you'll use it as `DATABASE_URL`. Make sure the URL includes `?sslmode=require`.

### 3. Deploy the web service

1. In the Render dashboard, click **New → Blueprint** and connect your GitHub repo. Render picks up `render.yaml` automatically.
2. Under **Secret Files**, upload your `gcp-service-account.json` key file with the filename `gcp-service-account.json`. Render makes it available at `/etc/secrets/gcp-service-account.json`.
3. Set the following environment variables in the Render dashboard (marked `sync: false` in `render.yaml`, so they must be set manually):

   | Variable             | Value                                              |
   | -------------------- | -------------------------------------------------- |
   | `FLASK_SECRET_KEY`   | A random 32-byte hex string                        |
   | `JWT_SECRET_KEY`     | A different random 32-byte hex string              |
   | `DATABASE_URL`       | Internal Database URL from step 2                  |
   | `GROQ_API_KEY`       | Groq API key (preferred — free tier)               |
   | `OPENAI_API_KEY`     | OpenAI key (fallback if Groq not set)              |
   | `VAPID_PRIVATE_KEY`  | VAPID private key for push notifications           |
   | `VAPID_PUBLIC_KEY`   | VAPID public key for push notifications            |
   | `VAPID_CLAIMS_EMAIL` | Contact email sent with push notification requests |

   Generate Flask/JWT secret keys with:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Generate a fresh VAPID key pair with:

   ```bash
   uv run python -m py_vapid --gen
   ```

4. Trigger a deploy. Render runs `flask db upgrade` on startup (configured in the Dockerfile).

### 4. Verify

- Visit your Render URL and register an account.
- Add a pantry item with a photo — confirm the image loads from `storage.googleapis.com`.
- Check Render logs for any errors.

## Repository Layout

- `app/` — Flask application package
  - `auth/` — login / register routes and forms
  - `perishables/` — pantry item CRUD
  - `recipes/` — recipe search and display
  - `api/` — JWT-auth REST endpoints
  - `recognition/` — AI vision service for item identification
  - `notifications/` — Web Push scheduler
  - `onboarding/` — onboarding flows
  - `main/` — landing page routes
  - `ingredient_normalization.py` — fuzzy ingredient matching
  - `logging_config.py` — structured logging setup
  - `storage.py` — photo storage abstraction (GCS / local)
- `config.py` — application configuration
- `wsgi.py` — application entry point
- `migrations/` — Alembic migration files
- `templates/`, `static/` — frontend templates and assets
- `.env.example` — environment variables template
- `render.yaml` — Render deployment blueprint
- `docs/` — project documentation and design notes

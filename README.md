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

## Configuration

Copy the environment template and edit values as needed:

```bash
cp -n .env.example .env
```

Key environment variables:

- `FLASK_SECRET_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `LOG_LEVEL`
- `FLASK_ENV`
- `ALLOWED_ORIGINS`

## Development Commands

- `make dev` — run the development server
- `make setup` — install dependencies, install Git hooks, and run migrations
- `make migrate msg="Your message"` — create and apply a new migration

## Repository Layout

- `app/` — Flask application package
- `config.py` — application configuration
- `wsgi.py` — application entry point
- `migrations/` — Alembic migration files
- `templates/`, `static/` — frontend templates and assets
- `.env.example` — environment variables template
- `docs/` — project documentation and design notes

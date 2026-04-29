# Asian Auntie — Claude Code Guide

## Project overview

Asian Auntie is a Flask web app that helps users track perishable pantry items and discover Asian recipes that use what they have. Users photograph or scan pantry items; AI recognition extracts the name and expiry date; a recipe engine suggests what to cook.

## Tech stack

- **Backend**: Python / Flask, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate (Alembic), Flask-JWT-Extended
- **Database**: SQLite in dev, Postgres-compatible in prod
- **AI**: OpenAI API (vision) for item recognition via `app/recognition/`
- **Frontend**: Server-rendered Jinja2 templates, vanilla JS, no build step
- **Package manager**: `uv` (not pip/poetry)

## Common commands

```bash
make dev          # run dev server on :8080
make setup        # install deps, configure pre-commit, apply migrations
make migrate msg="describe change"  # generate + apply a migration
```

Or directly:

```bash
uv run flask --app wsgi run --debug
uv run flask --app wsgi db upgrade
uv run flask --app wsgi db migrate -m "..."
```

## Project layout

```
app/
  __init__.py          # app factory
  models.py            # SQLAlchemy models
  extensions.py        # db, login_manager, etc.
  auth/                # login / register routes + forms
  perishables/         # pantry item CRUD (main feature)
    routes.py
    forms.py           # AddItemForm, PANTRY_ITEMS, LOCATIONS, ITEM_TYPES
  recipes/             # recipe search + display
  api/                 # JWT-auth REST endpoints
  recognition/         # OpenAI vision service for item identification
  notifications/       # Web Push scheduler
config.py              # Config / DevelopmentConfig / ProductionConfig
migrations/versions/   # Alembic migration files
templates/             # Jinja2 templates
static/                # CSS, JS, icons
uploads/               # user-uploaded photos (gitignored)
pipeline/              # offline recipe scraping pipeline
```

## Data model — Item

Key fields on the `Item` model (`app/models.py`):

| Column           | Type        | Notes                                                                                                   |
| ---------------- | ----------- | ------------------------------------------------------------------------------------------------------- |
| `name`           | String(256) | Raw name as entered/recognised (e.g. "Creamises Kokomilch")                                             |
| `standard_name`  | String(256) | Canonical pantry ingredient mapped from `PANTRY_ITEMS` (e.g. "Coconut milk") — used for recipe matching |
| `item_type`      | String(32)  | Enum: sauce, oil, spice, condiment, produce, dried, tofu, seafood, dairy, other, unknown                |
| `location`       | String(32)  | Storage location: fridge, freezer, pantry, cupboard, counter                                            |
| `barcode`        | String(64)  | Raw barcode value if item was identified via barcode scan                                               |
| `expiry_date`    | Date        |                                                                                                         |
| `removed_at`     | DateTime    | Null while active; set on use/discard/mistake                                                           |
| `removal_reason` | String(32)  | used, discarded, unwanted, mistake                                                                      |

## Item add flow

Three paths all converge at a `step=confirm` POST that creates the item:

1. **Photo** — user takes photos → AI recognition → confirm card pre-filled
2. **Barcode** — JS scans barcode → `barcode_lookup` endpoint hits Open Food Facts → `barcode_confirm` step → confirm card
3. **Manual** — plain form, no recognition

`standard_name` is auto-populated via `_fuzzy_standard_name()` in `routes.py` using the same subsequence-matching algorithm as the frontend autocomplete. Users can override it in the confirm/manual form.

## PANTRY_ITEMS list

The canonical ingredient list lives in `app/perishables/forms.py` as `PANTRY_ITEMS`. It is imported by routes (for server-side fuzzy matching) and mirrored inline in `add_item.html` (for the client-side autocomplete). **Keep both in sync** when adding entries.

## Migrations

Always use `batch_alter_table` for SQLite compatibility:

```python
def upgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.add_column(sa.Column("my_col", sa.String(64), nullable=True))
```

Revision IDs must be unique across all files in `migrations/versions/`. The current head is `c9d0e1f2a3b4`.

## Environment variables

See `.env.example`. Key vars:

- `FLASK_SECRET_KEY`
- `DATABASE_URL` (defaults to SQLite)
- `OPENAI_API_KEY` — required for photo recognition
- `VAPID_PRIVATE_KEY` / `VAPID_PUBLIC_KEY` — for Web Push notifications

## Style conventions

- No comments unless the _why_ is non-obvious
- No trailing summaries in AI responses
- `uv` for all Python tooling, never `pip` directly

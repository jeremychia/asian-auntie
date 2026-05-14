"""
Promote items (and their photos) from the local dev SQLite database to prod.

Pass config via a YAML file (--config migration.yaml) or env vars.

YAML keys (all flat, matching env var names):
    Required:
        dev_username           username in the dev database (source)
        prod_username          username in the prod database (target)
        prod_database_url      production PostgreSQL connection string
        prod_gcs_bucket_name   GCS bucket to upload photos into

    Optional:
        dev_db                 path to dev SQLite file (default: instance/app.db)
        dev_uploads_dir        path to local uploads folder (default: uploads/)
        dev_gcs_credentials_json    service-account key JSON string for dev GCS photos
        prod_gcs_credentials_json   service-account key JSON string; omit to use ADC

Usage:
    uv run scripts/migrate_dev_to_prod.py --config migration.yaml [--all] [--dry-run]
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

from sqlalchemy import create_engine, text

ITEM_COLUMNS = [
    "name",
    "item_type",
    "expiry_date",
    "confidence_score",
    "cache_hit",
    "date_added",
    "location",
    "standard_name",
    "barcode",
    "quantity_state",
    "removed_at",
    "removal_reason",
    "brands",
    "quantity",
    "ingredients_text",
    "labels_tags",
    "product_data_source",
    "off_nutriscore_grade",
    "off_nutriscore_score",
    "off_nova_group",
    "off_ecoscore_grade",
    "off_ecoscore_score",
    "off_categories_tags",
    "off_allergens_tags",
    "off_packaging_tags",
    "off_data_quality_tags",
]

PHOTO_COLUMNS = ["photo_type", "display_order", "created_at"]


def _rewrite_pg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _gcs_client(credentials_json: str | None):
    from google.cloud import storage as gcs

    if credentials_json:
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json)
        )
        return gcs.Client(credentials=creds)
    return gcs.Client()


def _upload_to_gcs(
    image_bytes: bytes,
    object_name: str,
    bucket_name: str,
    credentials_json: str | None,
) -> str:
    client = _gcs_client(credentials_json)
    blob = client.bucket(bucket_name).blob(object_name)
    blob.upload_from_string(image_bytes, content_type="image/jpeg")
    return blob.public_url


def _read_local_photo(path: str, uploads_dir: Path) -> bytes | None:
    full_path = uploads_dir / path
    if not full_path.exists():
        return None
    return full_path.read_bytes()


def _read_gcs_photo(
    url: str, credentials_json: str | None
) -> tuple[bytes | None, str | None]:
    """Download a photo from GCS. Returns (bytes, None) on success or (None, error_msg) on failure."""
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read(), None
    except Exception as e:
        unauth_error = str(e)

    # Fall back to authenticated GCS download
    try:
        parts = url.replace("https://storage.googleapis.com/", "").split("/", 1)
        if len(parts) != 2:
            return None, f"unauthenticated: {unauth_error} | could not parse GCS URL"
        bucket_name, object_name = parts
        blob = _gcs_client(credentials_json).bucket(bucket_name).blob(object_name)
        return blob.download_as_bytes(), None
    except Exception as e:
        return None, f"unauthenticated: {unauth_error} | authenticated: {e}"

    return None


def _load_config(config_path: str | None) -> dict:
    """Load config from YAML file, falling back to env vars for any missing keys."""
    cfg: dict = {}
    if config_path:
        import yaml

        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}

    def _get(key: str, default: str | None = None) -> str | None:
        return cfg.get(key) or os.environ.get(key.upper()) or default

    def _require(key: str) -> str:
        val = _get(key)
        if not val:
            src = f"YAML key '{key}' or env var '{key.upper()}'"
            sys.exit(f"ERROR: {src} is required but not set.")
        return val

    def _resolve_creds(key: str) -> str | None:
        """Return credentials JSON string, reading from file if value is a path."""
        val = _get(key)
        if not val:
            return None
        candidate = Path(val)
        if not val.strip().startswith("{") and candidate.exists():
            return candidate.read_text().strip()
        return val

    project_root = Path(__file__).parent.parent
    return {
        "dev_username": _require("dev_username"),
        "prod_username": _require("prod_username"),
        "prod_url": _require("prod_database_url"),
        "prod_bucket": _require("prod_gcs_bucket_name"),
        "dev_db": _get("dev_db", str(project_root / "instance" / "app.db")),
        "uploads_dir": _get("dev_uploads_dir", str(project_root / "uploads")),
        "dev_gcs_creds": _resolve_creds("dev_gcs_credentials_json"),
        "prod_gcs_creds": _resolve_creds("prod_gcs_credentials_json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate dev items + photos to prod")
    parser.add_argument(
        "--config",
        metavar="FILE",
        help="YAML config file (see script docstring for keys)",
    )
    parser.add_argument(
        "--all",
        dest="include_removed",
        action="store_true",
        help="Include removed items (default: active only)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print migration plan without writing anything",
    )
    args = parser.parse_args()

    cfg = _load_config(args.config)

    prod_url = cfg["prod_url"]
    prod_bucket = cfg["prod_bucket"]
    dev_username = cfg["dev_username"]
    prod_username = cfg["prod_username"]
    prod_gcs_creds = cfg["prod_gcs_creds"]
    dev_gcs_creds = cfg["dev_gcs_creds"]
    uploads_dir = Path(cfg["uploads_dir"])

    dev_db_path = Path(cfg["dev_db"])
    if not dev_db_path.exists():
        sys.exit(f"ERROR: Dev database not found at {dev_db_path}")

    dev_engine = create_engine(f"sqlite:///{dev_db_path}")
    prod_engine = create_engine(_rewrite_pg_url(prod_url))

    with dev_engine.connect() as dev_conn, prod_engine.connect() as prod_conn:
        # Resolve user IDs
        dev_user_row = dev_conn.execute(
            text("SELECT id FROM users WHERE username = :u"), {"u": dev_username}
        ).fetchone()
        if not dev_user_row:
            sys.exit(f"ERROR: User '{dev_username}' not found in dev database.")
        dev_user_id = dev_user_row.id

        prod_user_row = prod_conn.execute(
            text("SELECT id FROM users WHERE username = :u"), {"u": prod_username}
        ).fetchone()
        if not prod_user_row:
            sys.exit(f"ERROR: User '{prod_username}' not found in prod database.")
        prod_user_id = prod_user_row.id

        print(f"Source : {dev_username} (dev id={dev_user_id})")
        print(f"Target : {prod_username} (prod id={prod_user_id})")
        print()

        # Fetch dev items for this user
        where = f"WHERE user_id = {dev_user_id}"
        if not args.include_removed:
            where += " AND removed_at IS NULL"
        dev_items = dev_conn.execute(
            text(f"SELECT * FROM items {where} ORDER BY date_added")
        ).fetchall()

        if not dev_items:
            print("No items found in dev database matching the filter.")
            return

        # Existing prod items for dedup: keyed by (name, expiry_date, date_added)
        existing_items = set()
        for row in prod_conn.execute(
            text(
                "SELECT name, expiry_date, date_added FROM items WHERE user_id = :uid"
            ),
            {"uid": prod_user_id},
        ):
            existing_items.add((row.name, str(row.expiry_date), str(row.date_added)))

        item_col_placeholders = ", ".join(f":{c}" for c in ITEM_COLUMNS)
        item_col_names = ", ".join(ITEM_COLUMNS)
        item_insert_sql = text(
            f"INSERT INTO items (user_id, {item_col_names}) "
            f"VALUES (:user_id, {item_col_placeholders}) RETURNING id"
        )

        photo_col_placeholders = ", ".join(f":{c}" for c in PHOTO_COLUMNS)
        photo_col_names = ", ".join(PHOTO_COLUMNS)
        photo_insert_sql = text(
            f"INSERT INTO item_photos (item_id, photo_path, {photo_col_names}) "
            f"VALUES (:item_id, :photo_path, {photo_col_placeholders})"
        )

        items_migrated = items_skipped = photos_ok = photos_skipped = photos_error = 0

        for item in dev_items:
            item_dict = dict(item._mapping)
            dedup_key = (
                item_dict["name"],
                str(item_dict["expiry_date"]),
                str(item_dict["date_added"]),
            )

            if dedup_key in existing_items:
                items_skipped += 1
                continue

            dev_item_id = item_dict["id"]

            # Fetch photos for this item
            dev_photos = dev_conn.execute(
                text(
                    "SELECT * FROM item_photos WHERE item_id = :id ORDER BY display_order"
                ),
                {"id": dev_item_id},
            ).fetchall()

            if args.dry_run:
                print(
                    f"  WOULD INSERT  {item_dict['name']} "
                    f"exp={item_dict['expiry_date']} loc={item_dict.get('location')} "
                    f"({len(dev_photos)} photo(s))"
                )
                for photo in dev_photos:
                    p = dict(photo._mapping)
                    src = p["photo_path"]
                    src_type = "GCS" if src.startswith("https://") else "local"
                    print(f"              photo [{src_type}] {src[:80]}")
                items_migrated += 1
                photos_ok += len(dev_photos)
                continue

            # Insert item — cast SQLite integer booleans to Python bool for Postgres
            row_data = {c: item_dict.get(c) for c in ITEM_COLUMNS}
            if row_data["cache_hit"] is not None:
                row_data["cache_hit"] = bool(row_data["cache_hit"])
            row_data["user_id"] = prod_user_id
            result = prod_conn.execute(item_insert_sql, row_data)
            prod_item_id = result.fetchone()[0]
            existing_items.add(dedup_key)
            items_migrated += 1

            print(
                f"  INSERT  {item_dict['name']} exp={item_dict['expiry_date']} "
                f"→ prod item id={prod_item_id}"
            )

            # Upload photos
            for photo in dev_photos:
                p = dict(photo._mapping)
                src = p["photo_path"]
                filename = os.path.basename(src.rstrip("/"))
                object_name = f"users/{prod_user_id}/{filename}"

                # External URLs (e.g. Open Food Facts) are already public — copy as-is
                if src.startswith("https://") and "storage.googleapis.com" not in src:
                    photo_data = {c: p.get(c) for c in PHOTO_COLUMNS}
                    photo_data["item_id"] = prod_item_id
                    photo_data["photo_path"] = src
                    prod_conn.execute(photo_insert_sql, photo_data)
                    print(f"          photo (external) → {src[:80]}")
                    photos_ok += 1
                    continue

                if src.startswith("https://"):
                    image_bytes, read_error = _read_gcs_photo(src, dev_gcs_creds)
                else:
                    image_bytes = _read_local_photo(src, uploads_dir)
                    read_error = (
                        None if image_bytes is not None else "file not found locally"
                    )

                if image_bytes is None:
                    print(f"          SKIP photo: {src[:80]}")
                    print(f"               reason: {read_error}")
                    photos_skipped += 1
                    continue

                try:
                    gcs_url = _upload_to_gcs(
                        image_bytes, object_name, prod_bucket, prod_gcs_creds
                    )
                    photo_data = {c: p.get(c) for c in PHOTO_COLUMNS}
                    photo_data["item_id"] = prod_item_id
                    photo_data["photo_path"] = gcs_url
                    prod_conn.execute(photo_insert_sql, photo_data)
                    print(f"          photo → {gcs_url}")
                    photos_ok += 1
                except Exception as e:
                    print(f"          ERROR uploading photo {src[:60]}: {e}")
                    photos_error += 1

        if not args.dry_run:
            prod_conn.commit()

    action = "Would migrate" if args.dry_run else "Migrated"
    print(
        f"\n{action} {items_migrated} item(s) (skipped {items_skipped} duplicate(s)). "
        f"Photos: {photos_ok} uploaded, {photos_skipped} skipped, {photos_error} error(s)."
    )
    if args.dry_run:
        print("(dry run — nothing was written)")
    if photos_error:
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Promote items (and their photos) from prod PostgreSQL to the local dev SQLite database.

Pass config via a YAML file (--config migration.yaml) or env vars.

YAML keys (all flat, matching env var names):
    Required:
        prod_username          username in the prod database (source)
        dev_username           username in the dev database (target)
        prod_database_url      production PostgreSQL connection string
        prod_gcs_bucket_name   GCS bucket where prod photos live

    Optional:
        dev_db                 path to dev SQLite file (default: instance/app.db)
        dev_uploads_dir        path to local uploads folder (default: uploads/)
        dev_gcs_bucket_name    dev GCS bucket; if set, photos are uploaded there
                               instead of saved locally
        prod_gcs_credentials_json   service-account key JSON string for prod GCS; omit to use ADC
        dev_gcs_credentials_json    service-account key JSON string for dev GCS; omit to use ADC

Usage:
    uv run scripts/migrate_prod_to_dev.py --config migration.yaml [--all] [--dry-run]
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


def _download_from_prod_gcs(
    photo_path: str, bucket_name: str, credentials_json: str | None
) -> tuple[bytes | None, str | None]:
    """Download a photo given its photo_path value (object name or full GCS URL).
    Returns (bytes, None) on success or (None, error_msg) on failure.
    """
    prefix = f"https://storage.googleapis.com/{bucket_name}/"
    if photo_path.startswith(prefix):
        object_name = photo_path[len(prefix) :]
    elif photo_path.startswith("https://storage.googleapis.com/"):
        # Full URL for a different/unknown bucket — try unauthenticated fetch
        try:
            with urllib.request.urlopen(photo_path, timeout=30) as resp:
                return resp.read(), None
        except Exception as e:
            return None, f"unauthenticated fetch failed: {e}"
    else:
        object_name = photo_path

    try:
        blob = _gcs_client(credentials_json).bucket(bucket_name).blob(object_name)
        return blob.download_as_bytes(), None
    except Exception as e:
        return None, f"GCS download failed: {e}"


def _upload_to_dev_gcs(
    image_bytes: bytes,
    object_name: str,
    bucket_name: str,
    credentials_json: str | None,
) -> str:
    """Upload to dev GCS and return the object name (not a public URL)."""
    client = _gcs_client(credentials_json)
    blob = client.bucket(bucket_name).blob(object_name)
    blob.upload_from_string(image_bytes, content_type="image/jpeg")
    return object_name


def _save_local_photo(image_bytes: bytes, rel_path: str, uploads_dir: Path) -> None:
    dest = uploads_dir / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(image_bytes)


def _load_config(config_path: str | None) -> dict:
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
        val = _get(key)
        if not val:
            return None
        candidate = Path(val)
        if not val.strip().startswith("{") and candidate.exists():
            return candidate.read_text().strip()
        return val

    project_root = Path(__file__).parent.parent
    return {
        "prod_username": _require("prod_username"),
        "dev_username": _require("dev_username"),
        "prod_url": _require("prod_database_url"),
        "prod_bucket": _require("prod_gcs_bucket_name"),
        "dev_db": _get("dev_db", str(project_root / "instance" / "app.db")),
        "uploads_dir": _get("dev_uploads_dir", str(project_root / "uploads")),
        "dev_bucket": _get("dev_gcs_bucket_name"),
        "prod_gcs_creds": _resolve_creds("prod_gcs_credentials_json"),
        "dev_gcs_creds": _resolve_creds("dev_gcs_credentials_json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate prod items + photos to dev")
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
    prod_username = cfg["prod_username"]
    dev_username = cfg["dev_username"]
    prod_gcs_creds = cfg["prod_gcs_creds"]
    dev_bucket = cfg["dev_bucket"]
    dev_gcs_creds = cfg["dev_gcs_creds"]
    uploads_dir = Path(cfg["uploads_dir"])

    dev_db_path = Path(cfg["dev_db"])
    if not dev_db_path.exists():
        sys.exit(f"ERROR: Dev database not found at {dev_db_path}")

    photo_dest = (
        f"dev GCS bucket '{dev_bucket}'" if dev_bucket else f"local {uploads_dir}"
    )
    print(f"Photo destination : {photo_dest}")
    print()

    prod_engine = create_engine(_rewrite_pg_url(prod_url))
    dev_engine = create_engine(f"sqlite:///{dev_db_path}")

    with prod_engine.connect() as prod_conn, dev_engine.connect() as dev_conn:
        # Resolve user IDs
        prod_user_row = prod_conn.execute(
            text("SELECT id FROM users WHERE username = :u"), {"u": prod_username}
        ).fetchone()
        if not prod_user_row:
            sys.exit(f"ERROR: User '{prod_username}' not found in prod database.")
        prod_user_id = prod_user_row.id

        dev_user_row = dev_conn.execute(
            text("SELECT id FROM users WHERE username = :u"), {"u": dev_username}
        ).fetchone()
        if not dev_user_row:
            sys.exit(f"ERROR: User '{dev_username}' not found in dev database.")
        dev_user_id = dev_user_row.id

        print(f"Source : {prod_username} (prod id={prod_user_id})")
        print(f"Target : {dev_username} (dev id={dev_user_id})")
        print()

        # Fetch prod items for this user
        where = f"WHERE user_id = {prod_user_id}"
        if not args.include_removed:
            where += " AND removed_at IS NULL"
        prod_items = prod_conn.execute(
            text(f"SELECT * FROM items {where} ORDER BY date_added")
        ).fetchall()

        if not prod_items:
            print("No items found in prod database matching the filter.")
            return

        # Existing dev items for dedup: keyed by (name, expiry_date, date_added)
        existing_items = set()
        for row in dev_conn.execute(
            text(
                "SELECT name, expiry_date, date_added FROM items WHERE user_id = :uid"
            ),
            {"uid": dev_user_id},
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

        for item in prod_items:
            item_dict = dict(item._mapping)
            dedup_key = (
                item_dict["name"],
                str(item_dict["expiry_date"]),
                str(item_dict["date_added"]),
            )

            if dedup_key in existing_items:
                items_skipped += 1
                continue

            prod_item_id = item_dict["id"]

            # Fetch photos for this item
            prod_photos = prod_conn.execute(
                text(
                    "SELECT * FROM item_photos WHERE item_id = :id ORDER BY display_order"
                ),
                {"id": prod_item_id},
            ).fetchall()

            if args.dry_run:
                print(
                    f"  WOULD INSERT  {item_dict['name']} "
                    f"exp={item_dict['expiry_date']} loc={item_dict.get('location')} "
                    f"({len(prod_photos)} photo(s))"
                )
                for photo in prod_photos:
                    p = dict(photo._mapping)
                    src = p["photo_path"]
                    is_external = (
                        src.startswith("https://")
                        and "storage.googleapis.com" not in src
                    )
                    src_type = "external" if is_external else "GCS"
                    print(f"              photo [{src_type}] {src[:80]}")
                items_migrated += 1
                photos_ok += len(prod_photos)
                continue

            # Insert item — cast Postgres booleans to int for SQLite
            row_data = {c: item_dict.get(c) for c in ITEM_COLUMNS}
            if row_data["cache_hit"] is not None:
                row_data["cache_hit"] = int(bool(row_data["cache_hit"]))
            row_data["user_id"] = dev_user_id
            result = dev_conn.execute(item_insert_sql, row_data)
            dev_item_id = result.fetchone()[0]
            existing_items.add(dedup_key)
            items_migrated += 1

            print(
                f"  INSERT  {item_dict['name']} exp={item_dict['expiry_date']} "
                f"→ dev item id={dev_item_id}"
            )

            # Copy photos
            for photo in prod_photos:
                p = dict(photo._mapping)
                src = p["photo_path"]
                filename = os.path.basename(src.rstrip("/"))
                object_name = f"users/{dev_user_id}/{filename}"

                # External URLs (e.g. Open Food Facts) — keep as-is
                if src.startswith("https://") and "storage.googleapis.com" not in src:
                    photo_data = {c: p.get(c) for c in PHOTO_COLUMNS}
                    photo_data["item_id"] = dev_item_id
                    photo_data["photo_path"] = src
                    dev_conn.execute(photo_insert_sql, photo_data)
                    print(f"          photo (external) → {src[:80]}")
                    photos_ok += 1
                    continue

                # GCS photo — download from prod GCS first
                image_bytes, read_error = _download_from_prod_gcs(
                    src, prod_bucket, prod_gcs_creds
                )

                if image_bytes is None:
                    print(f"          SKIP photo: {src[:80]}")
                    print(f"               reason: {read_error}")
                    photos_skipped += 1
                    continue

                try:
                    if dev_bucket:
                        stored_path = _upload_to_dev_gcs(
                            image_bytes, object_name, dev_bucket, dev_gcs_creds
                        )
                        print(f"          photo → gs://{dev_bucket}/{stored_path}")
                    else:
                        _save_local_photo(image_bytes, object_name, uploads_dir)
                        stored_path = object_name
                        print(f"          photo → {uploads_dir / object_name}")

                    photo_data = {c: p.get(c) for c in PHOTO_COLUMNS}
                    photo_data["item_id"] = dev_item_id
                    photo_data["photo_path"] = stored_path
                    dev_conn.execute(photo_insert_sql, photo_data)
                    photos_ok += 1
                except Exception as e:
                    print(f"          ERROR copying photo {src[:60]}: {e}")
                    photos_error += 1

        if not args.dry_run:
            dev_conn.commit()

    action = "Would migrate" if args.dry_run else "Migrated"
    print(
        f"\n{action} {items_migrated} item(s) (skipped {items_skipped} duplicate(s)). "
        f"Photos: {photos_ok} copied, {photos_skipped} skipped, {photos_error} error(s)."
    )
    if args.dry_run:
        print("(dry run — nothing was written)")
    if photos_error:
        sys.exit(1)


if __name__ == "__main__":
    main()

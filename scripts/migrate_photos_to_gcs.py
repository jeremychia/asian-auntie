"""
One-off migration: upload local photos from uploads/ to GCS and update DB paths.

Usage:
    uv run python scripts/migrate_photos_to_gcs.py           # dry run
    uv run python scripts/migrate_photos_to_gcs.py --commit  # apply changes
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import ItemPhoto  # noqa: E402
from app.storage import upload_photo  # noqa: E402

dry_run = "--commit" not in sys.argv

app = create_app()

with app.app_context():
    bucket_name = app.config.get("GCS_BUCKET_NAME")
    if not bucket_name:
        print("GCS_BUCKET_NAME is not set — aborting")
        sys.exit(1)

    credentials_json = app.config.get("GCS_CREDENTIALS_JSON") or None
    upload_folder = app.config["UPLOAD_FOLDER"]

    photos = ItemPhoto.query.filter(~ItemPhoto.photo_path.startswith("https://")).all()

    print(
        f"{'DRY RUN — ' if dry_run else ''}Migrating {len(photos)} local photos to gs://{bucket_name}\n"
    )

    migrated = skipped = errors = 0

    for photo in photos:
        local_path = os.path.join(upload_folder, photo.photo_path)

        if not os.path.exists(local_path):
            print(f"  SKIP   {photo.photo_path} (file not found locally)")
            skipped += 1
            continue

        user_id = photo.item.user_id
        filename = os.path.basename(photo.photo_path)
        object_name = f"users/{user_id}/{filename}"

        try:
            if not dry_run:
                with open(local_path, "rb") as f:
                    image_bytes = f.read()
                gcs_url = upload_photo(
                    image_bytes, object_name, bucket_name, credentials_json
                )
                photo.photo_path = gcs_url
                db.session.add(photo)
                print(f"  OK     {local_path}\n         → {gcs_url}")
            else:
                print(
                    f"  WOULD  {local_path}\n         → gs://{bucket_name}/{object_name}"
                )
            migrated += 1
        except Exception as e:
            print(f"  ERROR  {photo.photo_path}: {e}")
            errors += 1

    print(
        f"\n{'Would migrate' if dry_run else 'Migrated'}: {migrated}  |  Skipped: {skipped}  |  Errors: {errors}"
    )

    if errors:
        sys.exit(1)

    if not dry_run and migrated > 0:
        db.session.commit()
        print("Database updated.")
    elif dry_run:
        print("\nRe-run with --commit to apply.")

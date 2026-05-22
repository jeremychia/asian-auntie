import json


def download_photo(
    object_name: str,
    bucket_name: str,
    credentials_json: str | None = None,
) -> bytes:
    """Download a GCS object and return its bytes."""
    from google.cloud import storage as gcs

    if credentials_json:
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json)
        )
        client = gcs.Client(credentials=creds)
    else:
        client = gcs.Client()
    return client.bucket(bucket_name).blob(object_name).download_as_bytes()


def delete_photo(
    object_name: str,
    bucket_name: str,
    credentials_json: str | None = None,
) -> None:
    """Delete a GCS object. Silent no-op if the object does not exist."""
    from google.cloud import storage as gcs

    if credentials_json:
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json)
        )
        client = gcs.Client(credentials=creds)
    else:
        client = gcs.Client()
    try:
        client.bucket(bucket_name).blob(object_name).delete()
    except Exception:
        pass


def upload_photo(
    image_bytes: bytes,
    object_name: str,
    bucket_name: str,
    credentials_json: str | None = None,
) -> str:
    """Upload image bytes to GCS and return the object name (not a public URL).

    Callers store the object name in ItemPhoto.photo_path; the /photo/<id>
    route serves it through an authenticated proxy so the bucket can stay private.
    """
    from google.cloud import storage as gcs

    if credentials_json:
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json)
        )
        client = gcs.Client(credentials=creds)
    else:
        client = gcs.Client()

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_bytes, content_type="image/jpeg")
    return object_name

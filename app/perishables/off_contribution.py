import json
import urllib.request
import urllib.parse
import urllib.error

from flask import current_app

from app.logging_config import get_logger

logger = get_logger(__name__)

_QUALITY_TAG_TO_FIELD = {
    "en:missing-brands": "brands",
    "en:missing-quantity": "quantity",
    "en:missing-ingredients": "ingredients_text",
    "en:missing-labels": "labels_tags",
}


def contribute_to_off(item) -> None:
    """
    Push missing OFF fields back to Open Food Facts for a barcode-scanned item.
    Only sends fields that OFF has flagged as missing via data_quality_tags.
    Fire-and-forget — swallows all exceptions so it never affects the user.
    NOT called from anywhere yet; wired up in a future release.
    """
    if not item.barcode:
        return

    username = current_app.config.get("OFF_USERNAME", "")
    password = current_app.config.get("OFF_PASSWORD", "")
    if not username or not password:
        return

    try:
        quality_tags = json.loads(item.off_data_quality_tags or "[]")
    except (json.JSONDecodeError, TypeError):
        return

    if not quality_tags:
        return

    payload = {
        "code": item.barcode,
        "user_id": username,
        "password": password,
    }

    for tag, field in _QUALITY_TAG_TO_FIELD.items():
        if tag in quality_tags:
            value = getattr(item, field, None)
            if value:
                payload[field.replace("_text", "").replace("_tags", "")] = value

    # Nothing new to contribute
    if len(payload) <= 3:
        return

    api_url = current_app.config.get("OFF_API_URL", "https://world.openfoodfacts.org")
    endpoint = f"{api_url}/cgi/product_jqm2.pl"

    try:
        encoded = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=encoded,
            method="POST",
            headers={
                "User-Agent": "AsianAuntie/1.0 (jeremyjchia@gmail.com)",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info(
                "off_contribution_sent",
                barcode=item.barcode,
                fields=list(payload.keys()),
                status=resp.status,
            )
    except Exception as exc:
        logger.warning("off_contribution_failed", barcode=item.barcode, error=str(exc))

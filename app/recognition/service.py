"""
Image recognition service — wraps a vision LLM API.

Provider priority (first match wins):
  1. Ollama   — OLLAMA_BASE_URL set (local dev, free)
  2. Groq     — GROQ_API_KEY set   (production, free tier, OpenAI-compatible)
  3. OpenAI   — OPENAI_API_KEY set (fallback)
  4. Stub     — no key set, returns zero-confidence result

Confidence routing (from docs/manage-perishables/flows.yaml):
  ≥ 0.85  → one-tap confirm (pre-filled card)
  0.60–0.85 → pre-filled card, expiry date field highlighted
  < 0.60  → empty form (name + expiry required)
"""

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.logging_config import get_logger

logger = get_logger(__name__)

VALID_ITEM_TYPES = {
    "sauce",
    "oil",
    "spice",
    "condiment",
    "produce",
    "dried",
    "tofu",
    "seafood",
    "dairy",
    "other",
    "unknown",
}

RECOGNITION_PROMPT = """
You are a food item recognition assistant for an Asian pantry management app.

Analyse the image and return a JSON object with exactly these fields:
{
  "name": "<item name, e.g. 'Fish sauce' or 'Gochujang'>",
  "item_type": "<one of: sauce, oil, spice, condiment, produce, dried, tofu, seafood, dairy, other, unknown>",
  "confidence": <float between 0.0 and 1.0>,
  "shelf_life_days": <integer estimate of shelf life in days, or null if unknown>,
  "printed_expiry_date": "<ISO date string YYYY-MM-DD if a printed best-before or expiry date is visible on the packaging, otherwise null>"
}

Rules:
- If you cannot identify the item clearly, set confidence below 0.6 and name to null.
- item_type must be exactly one of the listed values.
- printed_expiry_date must be in YYYY-MM-DD format or null.
- Return only the JSON object, no additional text.
"""


@dataclass
class RecognitionResult:
    name: Optional[str]
    item_type: str
    confidence: float
    shelf_life_days: Optional[int]
    printed_expiry_date: Optional[date]
    cache_hit: bool


def _stub_result() -> RecognitionResult:
    return RecognitionResult(
        name=None,
        item_type="unknown",
        confidence=0.0,
        shelf_life_days=None,
        printed_expiry_date=None,
        cache_hit=False,
    )


def recognize_items_multi(photos: list[tuple[bytes, str]]) -> RecognitionResult:
    """
    Run recognition on multiple photos and merge results.

    photos: list of (image_bytes, photo_type) where photo_type is one of
            barcode, appearance, label, other.

    Barcode-type results take priority over others when confidence >= 0.6.
    Among the remainder, the highest-confidence result wins.
    """
    if not photos:
        return _stub_result()
    if len(photos) == 1:
        return recognize_item(photos[0][0])

    results = [(recognize_item(img_bytes), ptype) for img_bytes, ptype in photos]

    barcode_results = [r for r, t in results if t == "barcode" and r.confidence >= 0.6]
    if barcode_results:
        return max(barcode_results, key=lambda r: r.confidence)

    return max((r for r, _ in results), key=lambda r: r.confidence)


def _resolve_provider() -> tuple[str, str, str | None]:
    """
    Return (provider_name, model, base_url) for the first configured provider.
    base_url is None for OpenAI (uses SDK default).
    """
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "")
    if ollama_url:
        return "ollama", "llama3.2-vision", f"{ollama_url.rstrip('/')}/v1"

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        return (
            "groq",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "https://api.groq.com/openai/v1",
        )

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        return "openai", "gpt-4o", None

    return "stub", "", None


def _resolve_api_key(provider: str) -> str:
    if provider == "ollama":
        return "ollama"
    if provider == "groq":
        return os.environ.get("GROQ_API_KEY", "")
    return os.environ.get("OPENAI_API_KEY", "")


def recognize_item(image_bytes: bytes) -> RecognitionResult:
    """
    Recognise a food item from an image.

    Provider is selected automatically from env vars — see module docstring.
    Returns a stub zero-confidence result when no provider is configured.
    """
    provider, model, base_url = _resolve_provider()
    if provider == "stub":
        logger.info("recognition_stub_mode", reason="no_provider_configured")
        return _stub_result()

    image_hash = hashlib.sha256(image_bytes).hexdigest()

    cached = _get_cached_result(image_hash)
    if cached:
        logger.info("recognition_cache_hit", image_hash=image_hash[:16])
        cached.cache_hit = True
        return cached

    try:
        api_key = _resolve_api_key(provider)
        result = _call_vision_api(
            api_key, base_url, model, provider, image_bytes, image_hash
        )
        _save_to_cache(image_hash, result)
        return result
    except Exception as exc:
        logger.error("recognition_api_error", provider=provider, error=str(exc))
        return _stub_result()


def _call_vision_api(
    api_key: str,
    base_url: str | None,
    model: str,
    provider: str,
    image_bytes: bytes,
    image_hash: str,
) -> RecognitionResult:
    import base64
    import time
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    resized = _resize_image(image_bytes)
    b64_image = base64.b64encode(resized).decode("utf-8")

    kwargs: dict = dict(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": RECOGNITION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}",
                            "detail": "low",
                        },
                    },
                ],
            }
        ],
        max_tokens=256,
    )
    # Groq and Ollama don't support response_format=json_object on all models
    if provider == "openai":
        kwargs["response_format"] = {"type": "json_object"}

    start = time.monotonic()
    response = client.chat.completions.create(**kwargs)
    latency_ms = round((time.monotonic() - start) * 1000)

    raw = response.choices[0].message.content
    data = json.loads(_extract_json(raw))

    printed_expiry = None
    if data.get("printed_expiry_date"):
        try:
            printed_expiry = date.fromisoformat(data["printed_expiry_date"])
        except ValueError:
            pass

    item_type = data.get("item_type", "unknown")
    if item_type not in VALID_ITEM_TYPES:
        item_type = "unknown"

    result = RecognitionResult(
        name=data.get("name"),
        item_type=item_type,
        confidence=float(data.get("confidence", 0.0)),
        shelf_life_days=data.get("shelf_life_days"),
        printed_expiry_date=printed_expiry,
        cache_hit=False,
    )

    logger.info(
        "recognition_api_call",
        provider=provider,
        model=model,
        image_hash=image_hash[:16],
        confidence=result.confidence,
        item_name=result.name,
        latency_ms=latency_ms,
    )
    return result


def _resize_image(image_bytes: bytes, max_size: int = 512) -> bytes:
    """Resize image to max_size x max_size to reduce API token cost."""
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85)
        return output.getvalue()
    except Exception:
        # If Pillow fails, send original — don't break the flow
        return image_bytes


def _extract_json(text: str) -> str:
    """Extract the first JSON object from text, handling prose-wrapped responses."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def _get_cached_result(image_hash: str) -> Optional[RecognitionResult]:
    """Check DB cache for a previous recognition result for this image."""
    try:
        from app.models import RecognitionCache

        record = RecognitionCache.query.filter_by(image_hash=image_hash).first()
        if record:
            data = json.loads(record.result_json)
            printed_expiry = None
            if data.get("printed_expiry_date"):
                try:
                    printed_expiry = date.fromisoformat(data["printed_expiry_date"])
                except ValueError:
                    pass
            return RecognitionResult(
                name=data.get("name"),
                item_type=data.get("item_type", "unknown"),
                confidence=float(data.get("confidence", 0.0)),
                shelf_life_days=data.get("shelf_life_days"),
                printed_expiry_date=printed_expiry,
                cache_hit=False,
            )
    except Exception:
        pass
    return None


def _save_to_cache(image_hash: str, result: RecognitionResult):
    """Persist a recognition result to the cache table."""
    try:
        from app.extensions import db
        from app.models import RecognitionCache

        payload = json.dumps(
            {
                "name": result.name,
                "item_type": result.item_type,
                "confidence": result.confidence,
                "shelf_life_days": result.shelf_life_days,
                "printed_expiry_date": (
                    result.printed_expiry_date.isoformat()
                    if result.printed_expiry_date
                    else None
                ),
            }
        )
        record = RecognitionCache(image_hash=image_hash, result_json=payload)
        db.session.add(record)
        db.session.commit()
    except Exception as exc:
        logger.warning("recognition_cache_write_failed", error=str(exc))

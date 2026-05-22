import json
import os
import hashlib
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone, date, timedelta
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image
from flask import (
    Blueprint,
    abort,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db, limiter
from app.models import Item, ItemPhoto
from app.perishables.forms import (
    AddItemForm,
    INGREDIENT_TYPE_MAP,
    ITEM_TYPES,
    PANTRY_ITEMS,
)
from app.notifications.routes import get_user_locations
from app.recognition.service import recognize_items_multi
from app.logging_config import get_logger
from app.ingredient_normalization import normalize_ingredient

perishables_bp = Blueprint("perishables", __name__)
logger = get_logger(__name__)


def _safe_next(url):
    parsed = urlparse(url)
    return url if (url and not parsed.netloc and url.startswith("/")) else None


# Open Food Facts family — tried in order; all share the same API structure
_OFF_DOMAINS = [
    "world.openfoodfacts.org",
    "world.openbeautyfacts.org",
    "world.openproductsfacts.org",
]

# Maps OFF categories_tags prefixes → item_type enum.
# Checked in order; first match wins.
_OFF_CATEGORY_MAP: list[tuple[frozenset[str], str]] = [
    (
        frozenset(
            {
                "en:dairy-products",
                "en:cheeses",
                "en:milks",
                "en:yogurts",
                "en:cream",
                "en:butter",
            }
        ),
        "dairy",
    ),
    (
        frozenset(
            {
                "en:sauces",
                "en:hot-sauces",
                "en:fish-sauces",
                "en:soy-sauces",
                "en:cooking-sauces",
                "en:pasta-sauces",
            }
        ),
        "sauce",
    ),
    (
        frozenset(
            {
                "en:oils-and-fats",
                "en:vegetable-oils",
                "en:cooking-oils",
                "en:olive-oils",
                "en:sesame-oils",
            }
        ),
        "oil",
    ),
    (frozenset({"en:spices", "en:herbs", "en:spice-mixes", "en:seasonings"}), "spice"),
    (
        frozenset(
            {
                "en:condiments",
                "en:vinegars",
                "en:mustards",
                "en:ketchup",
                "en:mayonnaises",
                "en:relishes",
            }
        ),
        "condiment",
    ),
    (
        frozenset(
            {
                "en:fresh-produce",
                "en:vegetables",
                "en:fruits",
                "en:fresh-vegetables",
                "en:fresh-fruits",
            }
        ),
        "produce",
    ),
    (
        frozenset(
            {
                "en:dried-products",
                "en:cereals",
                "en:legumes",
                "en:pasta",
                "en:rice",
                "en:noodles",
                "en:dried-foods",
            }
        ),
        "dried",
    ),
    (
        frozenset({"en:seafood", "en:fish", "en:shellfish", "en:fish-products"}),
        "seafood",
    ),
    (frozenset({"en:tofu", "en:soy-products", "en:tempeh"}), "tofu"),
]

_VALID_ITEM_TYPES = {k for k, _ in ITEM_TYPES}


def _get_user_item(item_id: int, include_removed: bool = False):
    """Fetch an active item owned by the current user, or 404."""
    query = Item.query.filter_by(id=item_id, user_id=current_user.id)
    if not include_removed:
        query = query.filter(Item.removed_at.is_(None))
    else:
        query = query.filter(Item.removed_at.isnot(None))
    return query.first_or_404()


def _map_off_categories(categories: list[str]) -> str:
    cat_set = set(categories)
    for keywords, item_type in _OFF_CATEGORY_MAP:
        if cat_set & keywords:
            return item_type
    return "other"


def _lookup_off(barcode: str) -> dict | None:
    """Query Open Food Facts family for a barcode. Returns the product dict or None."""
    for domain in _OFF_DOMAINS:
        url = f"https://{domain}/api/v2/product/{barcode}.json"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AsianAuntie/1.0 (jeremyjchia@gmail.com)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read())
                if body.get("status") == 1 and body.get("product"):
                    return body["product"]
        except Exception:
            continue
    return None


# Default shelf life by item type (days), used when recognition has no printed date
_SHELF_LIFE_DEFAULTS = {
    "produce": 5,
    "tofu": 7,
    "seafood": 7,
    "dairy": 7,
    "sauce": 180,
    "oil": 180,
    "condiment": 180,
    "dried": 180,
    "spice": 180,
    "other": 90,
    "unknown": 90,
}


def _save_photo_bytes(image_bytes: bytes, original_filename: str) -> str:
    """Compress and save image bytes to the upload folder, return the unique filename.

    Target: keep files under 100KB to optimize storage and bandwidth.
    """
    max_size_kb = 100
    quality = 85

    try:
        img = Image.open(BytesIO(image_bytes))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        compressed_buffer = BytesIO()
        img.save(compressed_buffer, format="JPEG", quality=quality, optimize=True)
        compressed_bytes = compressed_buffer.getvalue()

        while len(compressed_bytes) > max_size_kb * 1024 and quality > 50:
            quality -= 5
            compressed_buffer = BytesIO()
            img.save(compressed_buffer, format="JPEG", quality=quality, optimize=True)
            compressed_bytes = compressed_buffer.getvalue()
    except Exception:
        compressed_bytes = image_bytes

    filename = secure_filename(original_filename) or "photo.jpg"
    if not filename.lower().endswith((".jpg", ".jpeg")):
        filename = (
            filename.rsplit(".", 1)[0] + ".jpg"
            if "." in filename
            else filename + ".jpg"
        )

    content_hash = hashlib.sha256(compressed_bytes).hexdigest()[:16]
    unique_name = f"users/{current_user.id}/{content_hash}_{filename}"

    bucket_name = current_app.config.get("GCS_BUCKET_NAME")
    if bucket_name:
        from app.storage import upload_photo

        return upload_photo(
            compressed_bytes,
            unique_name,
            bucket_name,
            current_app.config.get("GCS_CREDENTIALS_JSON") or None,
        )

    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(compressed_bytes)
    return unique_name


def _save_item_photos(item_id: int, photo_data: list[dict]) -> None:
    """Create ItemPhoto records from a list of {path, type} dicts."""
    for i, pd in enumerate(photo_data):
        photo_type = pd.get("type", "appearance")
        if photo_type not in ItemPhoto.VALID_TYPES:
            photo_type = "appearance"
        db.session.add(
            ItemPhoto(
                item_id=item_id,
                photo_path=pd["path"],
                photo_type=photo_type,
                display_order=i,
            )
        )


@perishables_bp.route("/items/barcode_lookup", methods=["POST"])
@login_required
def barcode_lookup():
    data = request.get_json(silent=True) or {}
    barcode = str(data.get("barcode", "")).strip()

    if not barcode.isdigit() or not (8 <= len(barcode) <= 14):
        return jsonify({"error": "Invalid barcode"}), 400

    product = _lookup_off(barcode)
    if not product:
        return jsonify({"found": False})

    name = (product.get("product_name") or product.get("product_name_en") or "").strip()
    if not name:
        return jsonify({"found": False})

    categories = product.get("categories_tags") or []
    item_type = _map_off_categories(categories)
    shelf_life_days = _SHELF_LIFE_DEFAULTS.get(item_type, 90)

    _OFF_IMAGE_HOSTS = (
        "images.openfoodfacts.org",
        "images.openfoodfacts.net",
        "static.openfoodfacts.org",
    )

    def _is_safe_off_image_url(url):
        try:
            p = urlparse(url)
            return p.scheme == "https" and p.netloc in _OFF_IMAGE_HOSTS
        except Exception:
            return False

    image_path = None
    image_url = (
        product.get("image_front_url")
        or product.get("image_url")
        or product.get("image_front_small_url")
    )
    if image_url and _is_safe_off_image_url(image_url):
        try:
            req = urllib.request.Request(
                image_url,
                headers={"User-Agent": "AsianAuntie/1.0 (jeremyjchia@gmail.com)"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                image_bytes = resp.read()
            image_path = _save_photo_bytes(image_bytes, f"{barcode}.jpg")
        except Exception:
            image_path = image_url

    brands = (product.get("brands") or "").strip() or None
    quantity = (product.get("quantity") or "").strip() or None
    ingredients_text = (product.get("ingredients_text") or "").strip() or None
    labels_tags = json.dumps(product.get("labels_tags") or [])
    categories_tags = json.dumps(product.get("categories_tags") or [])
    allergens_tags = json.dumps(product.get("allergens_tags") or [])
    packaging_tags = json.dumps(product.get("packaging_tags") or [])
    data_quality_tags = json.dumps(product.get("data_quality_tags") or [])
    nutriscore_grade = (
        product.get("nutriscore_grade") or product.get("nutrition_grades") or ""
    ).upper()[:1] or None
    nutriscore_score_raw = product.get("nutriscore_score")
    nutriscore_score = (
        int(nutriscore_score_raw) if nutriscore_score_raw is not None else None
    )
    nova_group_raw = product.get("nova_group")
    nova_group = (
        int(nova_group_raw)
        if nova_group_raw is not None and str(nova_group_raw).isdigit()
        else None
    )
    ecoscore_grade = (product.get("ecoscore_grade") or "").lower()[:1] or None
    ecoscore_score_raw = product.get("ecoscore_score")
    ecoscore_score = int(ecoscore_score_raw) if ecoscore_score_raw is not None else None

    logger.info(
        "barcode_lookup",
        user_id=current_user.id,
        barcode=barcode,
        name=name,
        item_type=item_type,
        image_cached=image_path is not None,
    )
    return jsonify(
        {
            "found": True,
            "name": name,
            "item_type": item_type,
            "shelf_life_days": shelf_life_days,
            "image_path": image_path,
            "brands": brands,
            "quantity": quantity,
            "ingredients_text": ingredients_text,
            "labels_tags": labels_tags,
            "off_categories_tags": categories_tags,
            "off_allergens_tags": allergens_tags,
            "off_packaging_tags": packaging_tags,
            "off_data_quality_tags": data_quality_tags,
            "off_nutriscore_grade": nutriscore_grade,
            "off_nutriscore_score": nutriscore_score,
            "off_nova_group": nova_group,
            "off_ecoscore_grade": ecoscore_grade,
            "off_ecoscore_score": ecoscore_score,
        }
    )


@perishables_bp.route("/")
@perishables_bp.route("/dashboard")
@login_required
def dashboard():
    raw_items = (
        Item.query.filter_by(user_id=current_user.id)
        .filter(Item.removed_at.is_(None))
        .order_by(Item.expiry_date.asc())
        .all()
    )
    today = date.today()

    # Group by most-specific available key: barcode > standard_name > name.
    # defaultdict preserves insertion order (Python 3.7+) and raw_items is
    # already sorted by expiry_date, so items[0] in each group is always the
    # soonest-expiring — no re-sort needed.
    groups: dict = defaultdict(list)
    for item in raw_items:
        key = item.barcode or item.standard_name or item.name
        groups[key].append(item)

    grouped = [
        {
            "key": key,
            "items": items,
            "representative": items[0],
            "count": len(items),
        }
        for key, items in groups.items()
    ]

    all_expired = bool(grouped) and all(
        g["representative"].expiry_date < today for g in grouped
    )
    ghost_count = sum(1 for item in raw_items if item.ghost_level)
    return render_template(
        "perishables/dashboard.html",
        grouped=grouped,
        today=today,
        all_expired=all_expired,
        ghost_count=ghost_count,
    )


@perishables_bp.route("/items/group/<path:group_key>")
@login_required
def group_detail(group_key):
    today = date.today()
    items = (
        Item.query.filter(
            Item.user_id == current_user.id,
            Item.removed_at.is_(None),
            db.or_(
                Item.barcode == group_key,
                Item.standard_name == group_key,
                Item.name == group_key,
            ),
        )
        .order_by(Item.expiry_date.asc())
        .all()
    )
    if not items:
        abort(404)
    return render_template(
        "perishables/group_detail.html",
        items=items,
        group_key=group_key,
        today=today,
        tags=_parse_tags(items[0].labels_tags),
    )


@perishables_bp.route("/items/add", methods=["GET", "POST"])
@login_required
@limiter.limit("30 per hour", key_func=lambda: str(current_user.id), methods=["POST"])
def add_item():
    # ── GET: photo capture page (or skip directly to manual form) ─────────────
    if request.method == "GET":
        user_locs = get_user_locations(current_user)
        if request.args.get("skip"):
            return render_template(
                "perishables/add_item.html",
                step="manual",
                form=AddItemForm(),
                user_locations=user_locs,
                pantry_items=PANTRY_ITEMS,
                ingredient_type_map=INGREDIENT_TYPE_MAP,
            )
        return render_template(
            "perishables/add_item.html",
            step="photo",
            user_locations=user_locs,
            pantry_items=PANTRY_ITEMS,
            ingredient_type_map=INGREDIENT_TYPE_MAP,
        )

    step = request.form.get("step", "photo")
    logger.info(
        "add_item_post", step=step, num_files=len(request.files.getlist("photos"))
    )

    # ── POST step=photo: run recognition on all photos → show confirmation ────
    if step == "photo":
        photo_files = request.files.getlist("photos")
        photo_types = request.form.getlist("photo_types")

        logger.info("add_item_photo_start", num_files=len(photo_files))

        saved_photos = []  # list of {"path": str, "type": str, "bytes": bytes}
        for i, photo_file in enumerate(photo_files):
            if not (photo_file and photo_file.filename):
                logger.info("add_item_photo_skip", idx=i, reason="no_file_or_filename")
                continue
            image_bytes = photo_file.read()
            if not image_bytes:
                logger.info("add_item_photo_skip", idx=i, reason="empty_bytes")
                continue
            photo_type = photo_types[i] if i < len(photo_types) else "appearance"
            if photo_type not in ItemPhoto.VALID_TYPES:
                photo_type = "appearance"
            path = _save_photo_bytes(image_bytes, photo_file.filename)
            saved_photos.append(
                {"path": path, "type": photo_type, "bytes": image_bytes}
            )
            logger.info(
                "add_item_photo_saved",
                idx=i,
                photo_type=photo_type,
                size_bytes=len(image_bytes),
            )

        logger.info("add_item_photo_saved_count", count=len(saved_photos))

        if not saved_photos:
            logger.warning("add_item_photo_no_valid_photos")
            return render_template(
                "perishables/add_item.html",
                step="manual",
                form=AddItemForm(),
                user_locations=get_user_locations(current_user),
                pantry_items=PANTRY_ITEMS,
                ingredient_type_map=INGREDIENT_TYPE_MAP,
            )

        logger.info("add_item_recognition_start", num_photos=len(saved_photos))
        recognition = recognize_items_multi(
            [(p["bytes"], p["type"]) for p in saved_photos]
        )
        logger.info(
            "add_item_recognition_done",
            confidence=recognition.confidence if recognition else None,
            name=recognition.name if recognition else None,
        )

        confidence = recognition.confidence if recognition else 0.0
        form = AddItemForm()

        expiry_source = None
        if recognition and confidence >= 0.60 and recognition.name:
            form.name.data = recognition.name
            form.item_type.data = recognition.item_type
            if recognition.printed_expiry_date:
                form.expiry_date.data = recognition.printed_expiry_date
                expiry_source = "printed"
            elif recognition.shelf_life_days:
                form.expiry_date.data = date.today() + timedelta(
                    days=recognition.shelf_life_days
                )
                expiry_source = "estimated"
            else:
                form.expiry_date.data = date.today() + timedelta(
                    days=_SHELF_LIFE_DEFAULTS.get(recognition.item_type, 90)
                )
                expiry_source = "estimated"

        photo_data = [{"path": p["path"], "type": p["type"]} for p in saved_photos]
        form.photo_paths_json.data = json.dumps(photo_data)
        form.confidence_score.data = str(confidence)
        form.cache_hit.data = "1" if (recognition and recognition.cache_hit) else "0"
        form.source.data = "photo"
        if recognition and recognition.name:
            form.standard_name.data = normalize_ingredient(recognition.name)

        return render_template(
            "perishables/add_item.html",
            step="confirm",
            form=form,
            confidence=confidence,
            recognition=recognition,
            photo_items=photo_data,
            expiry_source=expiry_source,
            source="photo",
            user_locations=get_user_locations(current_user),
            pantry_items=PANTRY_ITEMS,
            ingredient_type_map=INGREDIENT_TYPE_MAP,
        )

    # ── POST step=barcode_confirm: barcode lookup result → show confirmation ──
    if step == "barcode_confirm":
        name = request.form.get("name", "").strip()
        item_type = request.form.get("item_type", "other")
        barcode_value = request.form.get("barcode", "").strip()
        try:
            shelf_life_days = int(request.form.get("shelf_life_days", 90))
        except (TypeError, ValueError):
            shelf_life_days = 90

        if item_type not in _VALID_ITEM_TYPES:
            item_type = "other"

        off_image_path = request.form.get("off_image_path", "").strip()
        photo_data = (
            [{"path": off_image_path, "type": "appearance"}] if off_image_path else []
        )

        form = AddItemForm()
        form.name.data = name
        form.item_type.data = item_type
        form.expiry_date.data = date.today() + timedelta(days=shelf_life_days)
        form.photo_paths_json.data = json.dumps(photo_data)
        form.confidence_score.data = "0.75"
        form.cache_hit.data = "0"
        form.source.data = "barcode"
        form.barcode.data = barcode_value
        form.standard_name.data = normalize_ingredient(name)
        form.brands.data = request.form.get("brands", "")
        form.quantity.data = request.form.get("quantity", "")
        form.ingredients_text.data = request.form.get("ingredients_text", "")
        form.labels_tags.data = request.form.get("labels_tags", "[]")
        form.product_data_source.data = "off"
        form.off_nutriscore_grade.data = request.form.get("off_nutriscore_grade", "")
        form.off_nutriscore_score.data = request.form.get("off_nutriscore_score", "")
        form.off_nova_group.data = request.form.get("off_nova_group", "")
        form.off_ecoscore_grade.data = request.form.get("off_ecoscore_grade", "")
        form.off_ecoscore_score.data = request.form.get("off_ecoscore_score", "")
        form.off_categories_tags.data = request.form.get("off_categories_tags", "[]")
        form.off_allergens_tags.data = request.form.get("off_allergens_tags", "[]")
        form.off_packaging_tags.data = request.form.get("off_packaging_tags", "[]")
        form.off_data_quality_tags.data = request.form.get(
            "off_data_quality_tags", "[]"
        )

        return render_template(
            "perishables/add_item.html",
            step="confirm",
            form=form,
            confidence=0.75,
            recognition=None,
            photo_items=photo_data,
            expiry_source="estimated",
            source="barcode",
            user_locations=get_user_locations(current_user),
            pantry_items=PANTRY_ITEMS,
            ingredient_type_map=INGREDIENT_TYPE_MAP,
        )

    # ── POST step=confirm: save item from confirmation card ───────────────────
    if step == "confirm":
        form = AddItemForm()
        if form.validate_on_submit():
            try:
                confidence_score = float(form.confidence_score.data)
            except (TypeError, ValueError):
                confidence_score = None
            cache_hit = (
                (form.cache_hit.data == "1") if confidence_score is not None else None
            )

            def _int_or_none(val):
                try:
                    return int(val) if val else None
                except (TypeError, ValueError):
                    return None

            item = Item(
                user_id=current_user.id,
                name=form.name.data.strip(),
                item_type=form.item_type.data,
                expiry_date=form.expiry_date.data,
                confidence_score=confidence_score,
                cache_hit=cache_hit,
                location=(
                    form.location.data.strip().lower() if form.location.data else None
                ),
                standard_name=form.standard_name.data
                or normalize_ingredient(form.name.data.strip()),
                barcode=form.barcode.data or None,
                brands=form.brands.data or None,
                quantity=form.quantity.data or None,
                ingredients_text=form.ingredients_text.data or None,
                labels_tags=form.labels_tags.data or None,
                product_data_source=form.product_data_source.data or None,
                off_nutriscore_grade=form.off_nutriscore_grade.data or None,
                off_nutriscore_score=_int_or_none(form.off_nutriscore_score.data),
                off_nova_group=_int_or_none(form.off_nova_group.data),
                off_ecoscore_grade=form.off_ecoscore_grade.data or None,
                off_ecoscore_score=_int_or_none(form.off_ecoscore_score.data),
                off_categories_tags=form.off_categories_tags.data or None,
                off_allergens_tags=form.off_allergens_tags.data or None,
                off_packaging_tags=form.off_packaging_tags.data or None,
                off_data_quality_tags=form.off_data_quality_tags.data or None,
            )
            db.session.add(item)
            db.session.flush()  # get item.id before creating photos

            try:
                photo_data = json.loads(form.photo_paths_json.data or "[]")
            except (json.JSONDecodeError, TypeError):
                photo_data = []

            confirm_photo_files = request.files.getlist("confirm_photos")
            confirm_photo_types = request.form.getlist("confirm_photo_types")
            for i, photo_file in enumerate(confirm_photo_files):
                if not (photo_file and photo_file.filename):
                    continue
                image_bytes = photo_file.read()
                if not image_bytes:
                    continue
                photo_type = (
                    confirm_photo_types[i]
                    if i < len(confirm_photo_types)
                    else "appearance"
                )
                if photo_type not in ItemPhoto.VALID_TYPES:
                    photo_type = "appearance"
                path = _save_photo_bytes(image_bytes, photo_file.filename)
                photo_data.append({"path": path, "type": photo_type})

            _save_item_photos(item.id, photo_data)
            db.session.commit()

            logger.info(
                "item_added",
                user_id=current_user.id,
                item_id=item.id,
                item_name=item.name,
                photo_count=len(photo_data),
                item_type=item.item_type,
                confidence_score=item.confidence_score,
                cache_hit=item.cache_hit,
            )
            flash(f'"{item.name}" added to your pantry.', "success")
            if "add_another" in request.form:
                return redirect(url_for("perishables.add_item"))
            return redirect(url_for("perishables.dashboard"))

        try:
            confidence = float(form.confidence_score.data or 0)
        except ValueError:
            confidence = 0.0
        try:
            photo_items = json.loads(form.photo_paths_json.data or "[]")
        except (json.JSONDecodeError, TypeError):
            photo_items = []
        return render_template(
            "perishables/add_item.html",
            step="confirm",
            form=form,
            confidence=confidence,
            recognition=None,
            photo_items=photo_items,
            source=form.source.data or "photo",
            user_locations=get_user_locations(current_user),
            pantry_items=PANTRY_ITEMS,
            ingredient_type_map=INGREDIENT_TYPE_MAP,
        )

    # ── POST step=manual: save item from manual form ──────────────────────────
    if step == "manual":
        form = AddItemForm()
        if form.validate_on_submit():
            item = Item(
                user_id=current_user.id,
                name=form.name.data.strip(),
                item_type=form.item_type.data,
                expiry_date=form.expiry_date.data,
                location=form.location.data or None,
                standard_name=normalize_ingredient(form.name.data.strip()),
                barcode=(
                    form.barcode.data.strip() or None if form.barcode.data else None
                ),
            )
            db.session.add(item)
            db.session.flush()

            manual_photo_files = request.files.getlist("manual_photos")
            manual_photo_data = []
            for photo_file in manual_photo_files:
                if not (photo_file and photo_file.filename):
                    continue
                image_bytes = photo_file.read()
                if not image_bytes:
                    continue
                path = _save_photo_bytes(image_bytes, photo_file.filename)
                manual_photo_data.append({"path": path, "type": "appearance"})
            _save_item_photos(item.id, manual_photo_data)
            db.session.commit()

            logger.info(
                "item_added",
                user_id=current_user.id,
                item_id=item.id,
                item_name=item.name,
                photo_count=len(item.photos),
                item_type=item.item_type,
            )
            flash(f'"{item.name}" added to your pantry.', "success")
            return redirect(url_for("perishables.dashboard"))

        return render_template(
            "perishables/add_item.html",
            step="manual",
            form=form,
            user_locations=get_user_locations(current_user),
            pantry_items=PANTRY_ITEMS,
            ingredient_type_map=INGREDIENT_TYPE_MAP,
        )

    return redirect(url_for("perishables.add_item"))


def _parse_tags(labels_tags_json: str | None) -> list[str]:
    """Parse labels_tags JSON into display-ready strings, stripping language prefixes."""
    if not labels_tags_json:
        return []
    try:
        raw = json.loads(labels_tags_json)
    except (json.JSONDecodeError, TypeError):
        return []
    result = []
    for tag in raw:
        if ":" in tag:
            tag = tag.split(":", 1)[1]
        tag = tag.replace("-", " ").capitalize()
        if tag:
            result.append(tag)
    return result


@perishables_bp.route("/items/<int:item_id>")
@login_required
def item_detail(item_id):
    item = _get_user_item(item_id)
    today = date.today()
    return render_template(
        "perishables/item_detail.html",
        item=item,
        today=today,
        is_editing=False,
        pantry_items_list=PANTRY_ITEMS,
        tags=_parse_tags(item.labels_tags),
    )


@perishables_bp.route("/items/<int:item_id>/fragment")
@login_required
def item_fragment(item_id):
    item = _get_user_item(item_id)
    today = date.today()
    return render_template(
        "perishables/item_fragment.html",
        item=item,
        today=today,
    )


@perishables_bp.route("/items/<int:item_id>/edit", methods=["GET"])
@login_required
def edit_item(item_id):
    item = _get_user_item(item_id)
    today = date.today()
    return render_template(
        "perishables/item_detail.html",
        item=item,
        today=today,
        is_editing=True,
        pantry_items_list=PANTRY_ITEMS,
        next_url=request.args.get("next"),
        tags=_parse_tags(item.labels_tags),
    )


@perishables_bp.route("/items/<int:item_id>/location", methods=["POST"])
@login_required
def update_location(item_id):
    item = _get_user_item(item_id)
    new_location = request.form.get("location", "").strip().lower()
    wants_json = request.headers.get("Accept") == "application/json"
    if len(new_location) > 32:
        if wants_json:
            return jsonify({"ok": False, "error": "Location name is too long."}), 400
        flash("Location name is too long.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    item.location = new_location or None
    db.session.commit()
    if wants_json:
        return jsonify({"ok": True})
    return redirect(url_for("perishables.item_detail", item_id=item_id))


_VALID_QUANTITY_STATES = {"full", "three_quarters", "half", "nearly_gone"}


@perishables_bp.route("/items/<int:item_id>/quantity", methods=["POST"])
@login_required
def update_quantity_state(item_id):
    item = _get_user_item(item_id)
    new_state = request.form.get("quantity_state", "").strip()
    if new_state not in _VALID_QUANTITY_STATES:
        flash("Invalid quantity state.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    item.quantity_state = new_state
    db.session.commit()
    return redirect(
        _safe_next(request.form.get("next"))
        or url_for("perishables.item_detail", item_id=item_id)
    )


@perishables_bp.route("/items/<int:item_id>/edit", methods=["POST"])
@login_required
def update_item(item_id):
    item = _get_user_item(item_id)
    new_name = request.form.get("name", "").strip()
    new_expiry = request.form.get("expiry_date", "").strip()
    new_item_type = request.form.get("item_type", "").strip()
    new_location = request.form.get("location", "").strip().lower()
    new_standard_name = request.form.get("standard_name", "").strip()
    new_barcode = request.form.get("barcode", "").strip()
    if not new_name or len(new_name) > 256:
        flash("Item name is required and must be under 256 characters.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    if new_standard_name and len(new_standard_name) > 256:
        flash("Ingredient name is too long.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    if new_barcode and len(new_barcode) > 64:
        flash("Barcode is too long.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    try:
        parsed_expiry = date.fromisoformat(new_expiry)
    except ValueError:
        flash("Invalid expiry date.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    if new_item_type not in _VALID_ITEM_TYPES:
        flash("Invalid item type.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    if len(new_location) > 32:
        flash("Location name is too long.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    name_changed = new_name != item.name
    if new_standard_name:
        item.standard_name = new_standard_name
    elif name_changed:
        item.standard_name = normalize_ingredient(new_name)
    item.name = new_name
    item.expiry_date = parsed_expiry
    item.item_type = new_item_type
    item.location = new_location or None
    item.barcode = new_barcode or None
    db.session.commit()
    return redirect(
        _safe_next(request.form.get("next"))
        or url_for("perishables.item_detail", item_id=item_id)
    )


@perishables_bp.route(
    "/items/<int:item_id>/photos/<int:photo_id>/type", methods=["POST"]
)
@login_required
def update_photo_type(item_id, photo_id):
    item = _get_user_item(item_id)
    photo = ItemPhoto.query.filter_by(id=photo_id, item_id=item.id).first_or_404()
    new_type = request.form.get("photo_type", "appearance")
    if new_type not in ItemPhoto.VALID_TYPES:
        new_type = "appearance"
    photo.photo_type = new_type
    db.session.commit()
    return redirect(url_for("perishables.edit_photos", item_id=item_id))


@perishables_bp.route("/items/<int:item_id>/photos", methods=["GET"])
@login_required
def edit_photos(item_id):
    item = _get_user_item(item_id)
    return render_template("perishables/edit_photos.html", item=item)


@perishables_bp.route("/items/<int:item_id>/photos/add", methods=["POST"])
@login_required
def add_photo(item_id):
    item = _get_user_item(item_id)
    photo_files = request.files.getlist("photos")
    photo_types = request.form.getlist("photo_types")
    next_order = len(item.photos)
    added = 0
    for i, pf in enumerate(photo_files):
        if not (pf and pf.filename):
            continue
        image_bytes = pf.read()
        if not image_bytes:
            continue
        photo_type = photo_types[i] if i < len(photo_types) else "appearance"
        if photo_type not in ItemPhoto.VALID_TYPES:
            photo_type = "appearance"
        path = _save_photo_bytes(image_bytes, pf.filename)
        db.session.add(
            ItemPhoto(
                item_id=item.id,
                photo_path=path,
                photo_type=photo_type,
                display_order=next_order + added,
            )
        )
        added += 1
    if added:
        db.session.commit()
        logger.info(
            "photo_added", user_id=current_user.id, item_id=item.id, count=added
        )
    return redirect(url_for("perishables.edit_photos", item_id=item_id))


@perishables_bp.route(
    "/items/<int:item_id>/photos/<int:photo_id>/delete", methods=["POST"]
)
@login_required
def delete_photo(item_id, photo_id):
    item = _get_user_item(item_id)
    photo = ItemPhoto.query.filter_by(id=photo_id, item_id=item.id).first_or_404()

    bucket_name = current_app.config.get("GCS_BUCKET_NAME")
    if bucket_name and photo.photo_path.startswith("https://"):
        try:
            from app.storage import delete_photo as gcs_delete

            prefix = f"https://storage.googleapis.com/{bucket_name}/"
            if photo.photo_path.startswith(prefix):
                gcs_delete(
                    photo.photo_path[len(prefix) :],
                    bucket_name,
                    current_app.config.get("GCS_CREDENTIALS_JSON") or None,
                )
        except Exception:
            logger.warning("gcs_delete_failed", photo_id=photo_id)
    elif not bucket_name:
        try:
            local = os.path.join(current_app.config["UPLOAD_FOLDER"], photo.photo_path)
            if os.path.exists(local):
                os.remove(local)
        except Exception:
            logger.warning("local_delete_failed", photo_id=photo_id)

    db.session.delete(photo)
    remaining = (
        ItemPhoto.query.filter_by(item_id=item.id)
        .filter(ItemPhoto.id != photo_id)
        .order_by(ItemPhoto.display_order)
        .all()
    )
    for idx, p in enumerate(remaining):
        p.display_order = idx
    db.session.commit()
    logger.info(
        "photo_deleted", user_id=current_user.id, item_id=item.id, photo_id=photo_id
    )
    return redirect(url_for("perishables.edit_photos", item_id=item_id))


@perishables_bp.route("/items/<int:item_id>/use", methods=["POST"])
@login_required
def mark_used(item_id):
    item = _get_user_item(item_id)
    item_name = item.name
    item_expiry = item.expiry_date.strftime("%-d %b")
    item.removed_at = datetime.now(timezone.utc)
    item.removal_reason = "used"
    db.session.commit()
    logger.info(
        "item_marked_used",
        user_id=current_user.id,
        item_id=item.id,
        item_name=item_name,
    )
    return redirect(
        url_for(
            "perishables.dashboard",
            undo=item.id,
            undo_name=item_name,
            undo_expiry=item_expiry,
        )
    )


@perishables_bp.route("/items/<int:item_id>/undo", methods=["POST"])
@login_required
def undo_use(item_id):
    item = _get_user_item(item_id, include_removed=True)
    item.removed_at = None
    item.removal_reason = None
    db.session.commit()
    logger.info(
        "item_use_undone",
        user_id=current_user.id,
        item_id=item.id,
        item_name=item.name,
    )
    flash(f'"{item.name}" restored to your pantry.', "success")
    return redirect(url_for("perishables.dashboard"))


@perishables_bp.route("/items/<int:item_id>/remove", methods=["POST"])
@login_required
def remove_item(item_id):
    item = _get_user_item(item_id)
    reason = request.form.get("reason", "unwanted")
    if reason not in ("discarded", "unwanted", "mistake"):
        reason = "unwanted"
    item_name = item.name
    today = date.today()
    days_overdue = (today - item.expiry_date).days if item.expiry_date < today else None
    item.removed_at = datetime.now(timezone.utc)
    item.removal_reason = reason
    db.session.commit()
    logger.info(
        "item_removed",
        user_id=current_user.id,
        item_id=item.id,
        item_name=item_name,
        item_type=item.item_type,
        expiry_date=item.expiry_date.isoformat(),
        days_overdue=days_overdue,
        reason=reason,
    )
    return redirect(url_for("perishables.dashboard", undo=item.id, undo_name=item_name))


@perishables_bp.route("/items/remove-expired", methods=["POST"])
@login_required
def remove_expired():
    today = date.today()
    expired = (
        Item.query.filter_by(user_id=current_user.id)
        .filter(Item.removed_at.is_(None))
        .filter(Item.expiry_date < today)
        .all()
    )
    count = len(expired)
    for item in expired:
        item.removed_at = datetime.now(timezone.utc)
        item.removal_reason = "discarded"
    db.session.commit()
    logger.info("bulk_remove_expired", user_id=current_user.id, count=count)
    flash(f"Removed {count} expired item{'s' if count != 1 else ''}.", "success")
    return redirect(url_for("perishables.dashboard"))


_VALID_ITEM_TYPES = {v for v, _ in ITEM_TYPES}
_VALID_FREQUENCIES = {"high", "medium", "low"}
_VALID_BULK_ACTIONS = {"used", "discard", "checkin", "relocate"}


@perishables_bp.route("/items/<int:item_id>/type", methods=["POST"])
@login_required
def update_type(item_id):
    item = _get_user_item(item_id)
    new_type = request.form.get("item_type", "").strip()
    if new_type not in _VALID_ITEM_TYPES:
        return jsonify({"ok": False, "error": "Invalid type."}), 400
    item.item_type = new_type
    db.session.commit()
    return jsonify({"ok": True})


@perishables_bp.route("/items/<int:item_id>/frequency", methods=["POST"])
@login_required
def update_frequency(item_id):
    item = _get_user_item(item_id)
    freq = request.form.get("usage_frequency", "").strip()
    item.usage_frequency = freq if freq in _VALID_FREQUENCIES else None
    db.session.commit()
    return jsonify({"ok": True})


@perishables_bp.route("/items/bulk-action", methods=["POST"])
@login_required
def bulk_action():
    raw_ids = request.form.getlist("item_ids")
    item_ids = [int(i) for i in raw_ids if i.strip().isdigit()]
    action = request.form.get("action", "").strip()

    if action not in _VALID_BULK_ACTIONS or not item_ids:
        return jsonify({"ok": False, "error": "Nothing to do."}), 400

    items = Item.query.filter(
        Item.id.in_(item_ids),
        Item.user_id == current_user.id,
        Item.removed_at.is_(None),
    ).all()
    now = datetime.now(timezone.utc)
    count = len(items)

    if action == "used":
        for item in items:
            item.removed_at = now
            item.removal_reason = "used"
    elif action == "discard":
        for item in items:
            item.removed_at = now
            item.removal_reason = "discarded"
    elif action == "checkin":
        for item in items:
            item.last_checked_at = now
    elif action == "relocate":
        new_location = request.form.get("new_location", "").strip().lower()
        if len(new_location) > 32:
            return jsonify({"ok": False, "error": "Location too long."}), 400
        for item in items:
            item.location = new_location or None

    db.session.commit()
    logger.info("bulk_action", user_id=current_user.id, action=action, count=count)
    return jsonify({"ok": True, "count": count, "action": action})


@perishables_bp.route("/audit")
@login_required
def audit():
    raw_items = (
        Item.query.filter_by(user_id=current_user.id)
        .filter(Item.removed_at.is_(None))
        .all()
    )

    _gl_order = {"red": 0, "amber": 1, None: 2}

    zones: dict = defaultdict(list)
    for item in raw_items:
        zones[item.location or "__unsorted__"].append(item)

    for key in zones:
        zones[key].sort(key=lambda i: (_gl_order[i.ghost_level], -i.staleness_days))

    sorted_zones = dict(
        sorted(
            zones.items(),
            key=lambda kv: (-sum(1 for i in kv[1] if i.ghost_level), -len(kv[1])),
        )
    )

    audit_json = {
        zone_key: [
            {
                "id": item.id,
                "name": item.name,
                "type": item.item_type or "unknown",
                "staleness": item.staleness_days,
                "expiry": item.expiry_date.isoformat() if item.expiry_date else None,
                "ghost": item.ghost_level,
                "location": item.location or "",
                "photo": item.display_photo.photo_url if item.display_photo else None,
            }
            for item in zone_items
        ]
        for zone_key, zone_items in sorted_zones.items()
    }

    ghost_count = sum(1 for i in raw_items if i.ghost_level)
    unsorted_count = sum(1 for i in raw_items if not i.location)

    return render_template(
        "perishables/audit.html",
        zones=sorted_zones,
        audit_json=audit_json,
        ghost_count=ghost_count,
        unsorted_count=unsorted_count,
        total_count=len(raw_items),
        user_locations=get_user_locations(current_user),
    )

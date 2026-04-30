import json
import os
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone, date, timedelta
from io import BytesIO
from PIL import Image
from flask import (
    Blueprint,
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

from app.extensions import db
from app.models import Item, ItemPhoto
from app.perishables.forms import AddItemForm, ITEM_TYPES, PANTRY_ITEMS
from app.recognition.service import recognize_items_multi
from app.logging_config import get_logger
from app.ingredient_normalization import normalize_ingredient

perishables_bp = Blueprint("perishables", __name__)
logger = get_logger(__name__)

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
    unique_name = f"{current_user.id}_{content_hash}_{filename}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
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

    image_path = None
    image_url = (
        product.get("image_front_url")
        or product.get("image_url")
        or product.get("image_front_small_url")
    )
    if image_url:
        try:
            req = urllib.request.Request(
                image_url,
                headers={"User-Agent": "AsianAuntie/1.0 (jeremyjchia@gmail.com)"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                image_bytes = resp.read()
            image_path = _save_photo_bytes(image_bytes, f"{barcode}.jpg")
        except Exception:
            image_path = None

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
        }
    )


@perishables_bp.route("/")
@perishables_bp.route("/dashboard")
@login_required
def dashboard():
    items = (
        Item.query.filter_by(user_id=current_user.id)
        .filter(Item.removed_at.is_(None))
        .order_by(Item.expiry_date.asc())
        .all()
    )
    today = date.today()
    all_expired = bool(items) and all(item.expiry_date < today for item in items)
    return render_template(
        "perishables/dashboard.html", items=items, today=today, all_expired=all_expired
    )


@perishables_bp.route("/items/add", methods=["GET", "POST"])
@login_required
def add_item():
    # ── GET: photo capture page (or skip directly to manual form) ─────────────
    if request.method == "GET":
        if request.args.get("skip"):
            return render_template(
                "perishables/add_item.html", step="manual", form=AddItemForm()
            )
        return render_template("perishables/add_item.html", step="photo")

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
                "perishables/add_item.html", step="manual", form=AddItemForm()
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

        return render_template(
            "perishables/add_item.html",
            step="confirm",
            form=form,
            confidence=0.75,
            recognition=None,
            photo_items=photo_data,
            expiry_source="estimated",
            source="barcode",
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
            )
            db.session.add(item)
            db.session.flush()  # get item.id before creating photos

            try:
                photo_data = json.loads(form.photo_paths_json.data or "[]")
            except (json.JSONDecodeError, TypeError):
                photo_data = []
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

            if form.photo.data and form.photo.data.filename:
                image_bytes = form.photo.data.read()
                path = _save_photo_bytes(image_bytes, form.photo.data.filename)
                db.session.add(
                    ItemPhoto(
                        item_id=item.id,
                        photo_path=path,
                        photo_type="appearance",
                        display_order=0,
                    )
                )
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

        return render_template("perishables/add_item.html", step="manual", form=form)

    return redirect(url_for("perishables.add_item"))


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
    )


@perishables_bp.route("/items/<int:item_id>/location", methods=["POST"])
@login_required
def update_location(item_id):
    item = _get_user_item(item_id)
    new_location = request.form.get("location", "").strip().lower()
    if len(new_location) > 32:
        flash("Location name is too long.", "error")
        return redirect(url_for("perishables.item_detail", item_id=item_id))
    item.location = new_location or None
    db.session.commit()
    return redirect(url_for("perishables.item_detail", item_id=item_id))


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
    return redirect(url_for("perishables.item_detail", item_id=item_id))


@perishables_bp.route("/items/<int:item_id>/use", methods=["POST"])
@login_required
def mark_used(item_id):
    item = _get_user_item(item_id)
    item_name = item.name
    item.removed_at = datetime.now(timezone.utc)
    item.removal_reason = "used"
    db.session.commit()
    logger.info(
        "item_marked_used",
        user_id=current_user.id,
        item_id=item.id,
        item_name=item_name,
    )
    return redirect(url_for("perishables.dashboard", undo=item.id, undo_name=item_name))


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

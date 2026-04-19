import json
import os
import hashlib
from datetime import datetime, timezone, date, timedelta
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Item, ItemPhoto
from app.perishables.forms import AddItemForm
from app.recognition.service import recognize_items_multi
from app.logging_config import get_logger

perishables_bp = Blueprint("perishables", __name__)
logger = get_logger(__name__)

# Default shelf life by item type (days), used when recognition has no printed date
_SHELF_LIFE_DEFAULTS = {
    "produce": 7,
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
    """Write image bytes to the upload folder and return the unique filename."""
    filename = secure_filename(original_filename) or "photo.jpg"
    content_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
    unique_name = f"{current_user.id}_{content_hash}_{filename}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    with open(save_path, "wb") as f:
        f.write(image_bytes)
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

    # ── POST step=photo: run recognition on all photos → show confirmation ────
    if step == "photo":
        photo_files = request.files.getlist("photos")
        photo_types = request.form.getlist("photo_types")

        saved_photos = []  # list of {"path": str, "type": str, "bytes": bytes}
        for i, photo_file in enumerate(photo_files):
            if not (photo_file and photo_file.filename):
                continue
            image_bytes = photo_file.read()
            if not image_bytes:
                continue
            photo_type = photo_types[i] if i < len(photo_types) else "appearance"
            if photo_type not in ItemPhoto.VALID_TYPES:
                photo_type = "appearance"
            path = _save_photo_bytes(image_bytes, photo_file.filename)
            saved_photos.append(
                {"path": path, "type": photo_type, "bytes": image_bytes}
            )

        if not saved_photos:
            return render_template(
                "perishables/add_item.html", step="manual", form=AddItemForm()
            )

        recognition = recognize_items_multi(
            [(p["bytes"], p["type"]) for p in saved_photos]
        )

        confidence = recognition.confidence if recognition else 0.0
        form = AddItemForm()

        if recognition and confidence >= 0.60 and recognition.name:
            form.name.data = recognition.name
            form.item_type.data = recognition.item_type
            if recognition.printed_expiry_date:
                form.expiry_date.data = recognition.printed_expiry_date
            elif recognition.shelf_life_days:
                form.expiry_date.data = date.today() + timedelta(
                    days=recognition.shelf_life_days
                )
            else:
                form.expiry_date.data = date.today() + timedelta(
                    days=_SHELF_LIFE_DEFAULTS.get(recognition.item_type, 90)
                )

        photo_data = [{"path": p["path"], "type": p["type"]} for p in saved_photos]
        form.photo_paths_json.data = json.dumps(photo_data)
        form.confidence_score.data = str(confidence)
        form.cache_hit.data = "1" if (recognition and recognition.cache_hit) else "0"

        return render_template(
            "perishables/add_item.html",
            step="confirm",
            form=form,
            confidence=confidence,
            recognition=recognition,
            photo_items=photo_data,
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
    item = (
        Item.query.filter_by(id=item_id, user_id=current_user.id)
        .filter(Item.removed_at.is_(None))
        .first_or_404()
    )
    today = date.today()
    return render_template("perishables/item_detail.html", item=item, today=today)


@perishables_bp.route("/items/<int:item_id>/use", methods=["POST"])
@login_required
def mark_used(item_id):
    item = (
        Item.query.filter_by(id=item_id, user_id=current_user.id)
        .filter(Item.removed_at.is_(None))
        .first_or_404()
    )
    item.removed_at = datetime.now(timezone.utc)
    item.removal_reason = "used"
    db.session.commit()
    logger.info(
        "item_marked_used",
        user_id=current_user.id,
        item_id=item.id,
        item_name=item.name,
    )
    flash(f'"{item.name}" marked as used.', "success")
    return redirect(url_for("perishables.dashboard"))


@perishables_bp.route("/items/<int:item_id>/remove", methods=["POST"])
@login_required
def remove_item(item_id):
    item = (
        Item.query.filter_by(id=item_id, user_id=current_user.id)
        .filter(Item.removed_at.is_(None))
        .first_or_404()
    )
    reason = request.form.get("reason", "unwanted")
    if reason not in ("discarded", "unwanted"):
        reason = "unwanted"
    item.removed_at = datetime.now(timezone.utc)
    item.removal_reason = reason
    db.session.commit()
    logger.info("item_removed", user_id=current_user.id, item_id=item.id, reason=reason)
    flash(f'"{item.name}" removed from your pantry.', "success")
    return redirect(url_for("perishables.dashboard"))


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

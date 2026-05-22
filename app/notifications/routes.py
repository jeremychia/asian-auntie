import json
import os
from datetime import datetime, timezone

from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, logout_user
from pywebpush import WebPushException, webpush

from app.extensions import db
from app.notifications import notifications_bp


@notifications_bp.route("/notifications/subscribe", methods=["POST"])
@login_required
def subscribe():
    data = request.get_json(silent=True) or {}
    sub = data.get("subscription")
    if not sub:
        return jsonify({"error": "subscription required"}), 400
    current_user.push_subscription = json.dumps(sub)
    current_user.notifications_enabled = True
    db.session.commit()
    return jsonify({"ok": True})


@notifications_bp.route("/notifications/subscribe", methods=["DELETE"])
@login_required
def unsubscribe():
    current_user.push_subscription = None
    current_user.notifications_enabled = False
    db.session.commit()
    return jsonify({"ok": True})


@notifications_bp.route("/settings", methods=["GET"])
@login_required
def settings():
    from app.onboarding.routes import ALL_CUISINES, CUISINE_COUNTS

    cooking_days = (
        json.loads(current_user.cooking_days) if current_user.cooking_days else None
    )
    cuisine_prefs = (
        json.loads(current_user.cuisine_prefs) if current_user.cuisine_prefs else []
    )
    return render_template(
        "settings.html",
        cooking_days=cooking_days,
        notifications_enabled=current_user.notifications_enabled,
        all_cuisines=ALL_CUISINES,
        cuisine_counts=CUISINE_COUNTS,
        cuisine_prefs=cuisine_prefs,
        expired_items_days=current_user.expired_items_days,
        user_locations=get_user_locations(current_user),
        default_locations=_DEFAULT_LOCATIONS,
    )


@notifications_bp.route("/settings/cuisine-prefs", methods=["POST"])
@login_required
def save_cuisine_prefs():
    from app.onboarding.routes import ALL_CUISINES

    data = request.get_json(silent=True) or {}
    raw = data.get("cuisine_prefs", [])
    if not isinstance(raw, list):
        return jsonify({"error": "invalid cuisine_prefs"}), 400
    valid = set(ALL_CUISINES)
    current_user.cuisine_prefs = json.dumps([c for c in raw if c in valid])
    db.session.commit()
    return jsonify({"ok": True})


@notifications_bp.route("/settings/cooking-days", methods=["POST"])
@login_required
def save_cooking_days():
    data = request.get_json(silent=True) or {}
    days = data.get("cooking_days", [])
    if not isinstance(days, list) or not all(
        isinstance(d, int) and 0 <= d <= 6 for d in days
    ):
        return jsonify({"error": "invalid cooking_days"}), 400
    current_user.cooking_days = json.dumps(days)
    db.session.commit()
    return jsonify({"ok": True})


@notifications_bp.route("/settings/expired-items", methods=["POST"])
@login_required
def save_expired_items():
    data = request.get_json(silent=True) or {}
    days = data.get("days")
    if days is None or not isinstance(days, int):
        return jsonify({"error": "invalid days value"}), 400
    if days < 0 or days > 90:
        return jsonify({"error": "days must be between 0 and 90"}), 400
    current_user.expired_items_days = days
    db.session.commit()
    return jsonify({"ok": True})


_DEFAULT_LOCATIONS = ["Fridge", "Freezer", "Pantry", "Cupboard", "Counter"]


def get_user_locations(user):
    if user.custom_locations:
        try:
            locs = json.loads(user.custom_locations)
            if isinstance(locs, list) and locs:
                return locs
        except (json.JSONDecodeError, TypeError):
            pass
    return _DEFAULT_LOCATIONS


@notifications_bp.route("/settings/locations", methods=["POST"])
@login_required
def save_locations():
    data = request.get_json(silent=True) or {}
    locs = data.get("locations", [])
    if not isinstance(locs, list):
        return jsonify({"error": "invalid"}), 400
    cleaned = [str(loc).strip()[:32] for loc in locs if str(loc).strip()][:20]
    if not cleaned:
        current_user.custom_locations = None
    else:
        current_user.custom_locations = json.dumps(cleaned)
    db.session.commit()
    return jsonify({"ok": True})


@notifications_bp.route("/settings/delete-account", methods=["GET"])
@login_required
def delete_account_confirm():
    from app.models import Item, ItemPhoto, RecipeEngagement

    now = datetime.now(timezone.utc)
    joined = current_user.created_at
    if joined.tzinfo is None:
        joined = joined.replace(tzinfo=timezone.utc)
    days_since_joined = (now - joined).days

    items_tracked = Item.query.filter_by(user_id=current_user.id).count()
    items_used = Item.query.filter_by(
        user_id=current_user.id, removal_reason="used"
    ).count()
    recipes_explored = RecipeEngagement.query.filter_by(user_id=current_user.id).count()
    photo_count = (
        ItemPhoto.query.join(Item).filter(Item.user_id == current_user.id).count()
    )

    return render_template(
        "settings_delete.html",
        days_since_joined=days_since_joined,
        items_tracked=items_tracked,
        items_used=items_used,
        recipes_explored=recipes_explored,
        photo_count=photo_count,
    )


@notifications_bp.route("/settings/delete-account", methods=["POST"])
@login_required
def delete_account():
    if request.form.get("confirm") != "DELETE MY ACCOUNT":
        flash("Confirmation text didn't match. Account not deleted.", "error")
        return redirect(url_for("notifications.delete_account_confirm"))

    from app.models import Item, ItemPhoto, RecipeEngagement, RefreshToken

    user_id = current_user.id
    bucket_name = current_app.config.get("GCS_BUCKET_NAME")
    credentials_json = current_app.config.get("GCS_CREDENTIALS_JSON") or None

    # Collect and delete stored photos before removing DB rows
    photos = ItemPhoto.query.join(Item).filter(Item.user_id == user_id).all()
    for photo in photos:
        if bucket_name:
            try:
                from app.storage import delete_photo as gcs_delete

                path = photo.photo_path
                prefix = f"https://storage.googleapis.com/{bucket_name}/"
                if path.startswith(prefix):
                    path = path[len(prefix) :]
                gcs_delete(path, bucket_name, credentials_json)
            except Exception:
                pass
        else:
            try:
                local = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], photo.photo_path
                )
                if os.path.isfile(local):
                    os.remove(local)
            except Exception:
                pass

    RecipeEngagement.query.filter_by(user_id=user_id).delete()
    RefreshToken.query.filter_by(user_id=user_id).delete()
    # Item cascade deletes ItemPhoto rows via relationship
    Item.query.filter_by(user_id=user_id).delete()

    from app.models import User

    user = db.session.get(User, user_id)
    logout_user()
    db.session.delete(user)
    db.session.commit()

    flash(
        "Your account and all your data have been permanently deleted. "
        "Thanks for the time you spent here — take care.",
        "info",
    )
    return redirect(url_for("main.landing"))


def send_push_notification(user, title, body, url="/"):
    """Send a Web Push notification to a user. Returns True on success."""
    if not user.push_subscription or not user.notifications_enabled:
        return False
    try:
        sub = json.loads(user.push_subscription)
        webpush(
            subscription_info=sub,
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
            vapid_claims={
                "sub": f"mailto:{current_app.config['VAPID_CLAIMS_EMAIL']}",
            },
        )
        return True
    except WebPushException:
        return False

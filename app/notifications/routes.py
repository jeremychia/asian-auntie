import json

from flask import current_app, jsonify, request
from flask_login import current_user, login_required
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

"""
Notification scheduler — runs once daily (19:00 local server time).

For each user with notifications enabled, finds items expiring before or on
the next cooking day after today, and sends at most 2 push notifications.

Cooking-day logic (MANAGE-003):
  - User stores cooking_days as a JSON list of weekday ints (0=Mon, 6=Sun).
  - Notify the evening before the nearest cooking day where an item expires
    before the *following* cooking day.
  - If cooking_days is null, fall back to a 3-day window.
"""

import json
import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

MAX_NOTIFICATIONS_PER_RUN = 2


def _next_cooking_day(from_date: date, cooking_days: list[int]) -> date | None:
    """Return the soonest cooking day on or after from_date."""
    if not cooking_days:
        return None
    for offset in range(8):
        candidate = from_date + timedelta(days=offset)
        if candidate.weekday() in cooking_days:
            return candidate
    return None


def _cooking_day_window(cooking_days: list[int]) -> tuple[date, date]:
    """
    Return (notify_start, notify_end) — items expiring in [notify_start, notify_end]
    should be notified about tonight.

    The window spans: tomorrow through the cooking day *after* the next cooking day,
    so we catch items the user can use on the upcoming cooking day.
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_cd = _next_cooking_day(tomorrow, cooking_days)
    if next_cd is None:
        # Fallback: 3-day window
        return tomorrow, today + timedelta(days=3)
    following_cd = _next_cooking_day(next_cd + timedelta(days=1), cooking_days)
    window_end = (following_cd - timedelta(days=1)) if following_cd else next_cd
    return tomorrow, window_end


def _fallback_window() -> tuple[date, date]:
    today = date.today()
    return today + timedelta(days=1), today + timedelta(days=3)


def _format_notification(
    item_name: str, expiry: date, cooking_day: date | None
) -> tuple[str, str]:
    today = date.today()
    days_left = (expiry - today).days

    if days_left == 0:
        urgency = "expires today"
    elif days_left == 1:
        urgency = "expires tomorrow"
    else:
        urgency = f"expires in {days_left} days"

    if cooking_day:
        day_name = cooking_day.strftime("%A")
        body = f"{item_name} {urgency} — use it {day_name}?"
    else:
        body = f"{item_name} {urgency} — use it soon?"

    return "Time to use something up", body


def run_notifications(app):
    """Check all users and send expiry notifications. Called by the scheduler."""
    with app.app_context():
        from app.extensions import db
        from app.models import Item, User
        from app.notifications.routes import send_push_notification

        users = (
            db.session.query(User)
            .filter(User.notifications_enabled.is_(True))
            .filter(User.push_subscription.isnot(None))
            .all()
        )

        for user in users:
            try:
                cooking_days = (
                    json.loads(user.cooking_days) if user.cooking_days else None
                )
                if cooking_days:
                    window_start, window_end = _cooking_day_window(cooking_days)
                    next_cd = _next_cooking_day(
                        date.today() + timedelta(days=1), cooking_days
                    )
                else:
                    window_start, window_end = _fallback_window()
                    next_cd = None

                expiring_items = (
                    db.session.query(Item)
                    .filter(
                        Item.user_id == user.id,
                        Item.removed_at.is_(None),
                        Item.expiry_date >= window_start,
                        Item.expiry_date <= window_end,
                    )
                    .order_by(Item.expiry_date.asc())
                    .limit(MAX_NOTIFICATIONS_PER_RUN)
                    .all()
                )

                for item in expiring_items:
                    title, body = _format_notification(
                        item.name, item.expiry_date, next_cd
                    )
                    send_push_notification(user, title, body, url="/")
                    logger.info(
                        "notification_sent",
                        extra={"user_id": user.id, "item": item.name},
                    )

            except Exception:
                logger.exception("notification_job_error", extra={"user_id": user.id})


def start_scheduler(app):
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    # Run daily at 19:00 UTC — evening before cooking days
    _scheduler.add_job(run_notifications, "cron", hour=19, minute=0, args=[app])
    _scheduler.start()
    logger.info("notification_scheduler_started")

import json
from collections import Counter
from datetime import datetime, timezone

from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.onboarding import onboarding_bp
from app.recipes.data import RECIPES

# Cuisines available in the recipe corpus, with counts pre-computed at module load
CUISINE_COUNTS = dict(Counter(r["cuisine"] for r in RECIPES))
ALL_CUISINES = sorted(CUISINE_COUNTS.keys())

# Locations shown in the wizard.  The value is the stored code.
LOCATIONS = [
    ("Malaysia", "MY"),
    ("Singapore", "SG"),
    ("Thailand", "TH"),
    ("Vietnam", "VN"),
    ("Indonesia", "ID"),
    ("Philippines", "PH"),
    ("China / Hong Kong / Taiwan", "CN"),
    ("United Kingdom", "GB"),
    ("Other Europe (EU)", "EU"),
    ("Australia / New Zealand", "AU"),
    ("United States / Canada", "US"),
    ("Other", "OTHER"),
]

# Locations that require the full GDPR notice
GDPR_LOCATIONS = {"GB", "EU"}

HOUSEHOLD_SIZES = [
    ("Just me", "solo"),
    ("2–3 people", "2-3"),
    ("4–5 people", "4-5"),
    ("6 or more", "6+"),
]


@onboarding_bp.route("/onboarding", methods=["GET"])
@login_required
def index():
    if current_user.onboarding_done:
        return redirect(url_for("perishables.dashboard"))

    existing_prefs = (
        json.loads(current_user.cuisine_prefs) if current_user.cuisine_prefs else []
    )

    return render_template(
        "onboarding/index.html",
        locations=LOCATIONS,
        all_cuisines=ALL_CUISINES,
        cuisine_counts=CUISINE_COUNTS,
        household_sizes=HOUSEHOLD_SIZES,
        gdpr_locations=list(GDPR_LOCATIONS),
        existing_location=current_user.location or "",
        existing_prefs=existing_prefs,
        existing_household=current_user.household_size or "",
    )


@onboarding_bp.route("/onboarding", methods=["POST"])
@login_required
def save():
    location = request.form.get("location", "").strip()
    raw_cuisines = request.form.getlist("cuisine_prefs")
    household_size = request.form.get("household_size", "").strip()
    consented = request.form.get("consent") == "true"

    if not consented:
        return redirect(url_for("onboarding.index"))

    valid_locations = {code for _, code in LOCATIONS}
    valid_households = {code for _, code in HOUSEHOLD_SIZES}
    valid_cuisines = set(ALL_CUISINES)

    raw_other = request.form.get("other_cuisine_requests", "[]")
    try:
        other_cuisines = [
            str(c).strip()[:64] for c in json.loads(raw_other) if str(c).strip()
        ][:20]
    except (ValueError, TypeError):
        other_cuisines = []

    current_user.location = location if location in valid_locations else None
    current_user.cuisine_prefs = json.dumps(
        [c for c in raw_cuisines if c in valid_cuisines]
    )
    current_user.household_size = (
        household_size if household_size in valid_households else None
    )
    current_user.other_cuisine_requests = json.dumps(other_cuisines)
    current_user.gdpr_consent = True
    current_user.consent_date = datetime.now(timezone.utc)
    current_user.onboarding_done = True

    db.session.commit()
    return redirect(url_for("perishables.dashboard"))


@onboarding_bp.route("/onboarding/cuisine-preview")
@login_required
def cuisine_preview():
    """Return recipe counts for a given set of cuisines (for live wizard feedback)."""
    selected = request.args.getlist("cuisines")
    counts = {c: CUISINE_COUNTS.get(c, 0) for c in selected if c in CUISINE_COUNTS}
    total = sum(counts.values())
    return jsonify({"counts": counts, "total": total})

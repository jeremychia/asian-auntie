from datetime import date, datetime, timezone

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import Item, RecipeEngagement
from app.logging_config import get_logger
from app.recipes.data import RECIPES
from app.pantry_data import PANTRY_ITEMS
from app.recipes.search import (
    score_recipe,
    parse_cook_time,
    candidate_recipe_indices,
    _RECIPE_ID_TO_IDX,
)

recipes_bp = Blueprint("recipes", __name__)
logger = get_logger(__name__)


def _get_pantry_items(user, include_expired_days=None):
    """Get pantry items, optionally including expired items within N days."""
    today = date.today()
    query = (
        Item.query.filter_by(user_id=user.id)
        .filter(Item.removed_at.is_(None))
        .order_by(Item.name.asc())
    )

    if include_expired_days is None:
        include_expired_days = user.expired_items_days

    if include_expired_days > 0:
        from datetime import timedelta

        cutoff = today - timedelta(days=include_expired_days)
        query = query.filter(Item.expiry_date >= cutoff)
    else:
        query = query.filter(Item.expiry_date >= today)

    return query.all()


@recipes_bp.route("/recipes")
@login_required
def index():
    import json as _json

    pantry_items = _get_pantry_items(current_user)
    skipped_ids = [
        e.recipe_id
        for e in RecipeEngagement.query.filter_by(
            user_id=current_user.id, feedback="not_for_me"
        ).all()
    ]
    made_ids = [
        e.recipe_id
        for e in RecipeEngagement.query.filter_by(
            user_id=current_user.id, feedback="yes_made"
        ).all()
    ]
    cuisine_prefs = (
        _json.loads(current_user.cuisine_prefs) if current_user.cuisine_prefs else []
    )
    return render_template(
        "recipes/index.html",
        pantry_items=pantry_items,
        pantry_vocab=PANTRY_ITEMS,
        skipped_ids=skipped_ids,
        made_ids=made_ids,
        user_expired_items_days=current_user.expired_items_days,
        cuisine_prefs=cuisine_prefs,
    )


PAGE_SIZE = 10


@recipes_bp.route("/recipes/search", methods=["POST"])
@login_required
def search():
    data = request.get_json(silent=True) or {}
    ingredients: list[str] = [str(i).strip() for i in data.get("ingredients", []) if i]
    page: int = max(1, int(data.get("page", 1)))
    show_all: bool = bool(data.get("show_all", False))
    sort_param: str = str(data.get("sort", "match")).strip()
    cuisines: list[str] = [str(c).strip() for c in data.get("cuisines", []) if c]
    website: str = str(data.get("website", "")).strip()
    cook_time_min: int = int(data.get("cook_time_min", 0))
    cook_time_max: int = int(data.get("cook_time_max", 120))

    # Parse sort parameter (e.g., "quick_rev" -> sort="quick", reverse=True)
    sort_reverse = sort_param.endswith("_rev")
    sort = sort_param.replace("_rev", "")

    if not ingredients:
        return jsonify({"results": [], "total": 0, "has_more": False})

    candidates = candidate_recipe_indices(ingredients)

    results = []
    for idx in candidates:
        recipe = RECIPES[idx]
        # Apply cuisine filter
        if cuisines and recipe.get("cuisine", "") not in cuisines:
            continue
        # Apply website filter
        if website and recipe.get("source", "") != website:
            continue
        # Apply cooking time filter
        recipe_time_mins = parse_cook_time(recipe.get("cook_time", ""))
        if recipe_time_mins is not None:
            if recipe_time_mins < cook_time_min or recipe_time_mins > cook_time_max:
                continue

        scored = score_recipe(recipe, idx, ingredients)
        if scored:
            results.append(scored)

    # Apply sort strategy
    if sort == "quick":
        results.sort(
            key=lambda r: (
                parse_cook_time(r.get("cook_time", "")) or 999,
                -r["match_pct"],
            ),
            reverse=sort_reverse,
        )
    elif sort == "simple":
        results.sort(
            key=lambda r: (r["total_count"], -r["match_pct"]), reverse=sort_reverse
        )
    else:  # match (default)
        results.sort(
            key=lambda r: (-r["match_pct"], r["total_count"]), reverse=sort_reverse
        )

    total = len(results)
    if show_all:
        page_results = results
        has_more = False
    else:
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_results = results[start:end]
        has_more = end < total

    logger.info(
        "recipe_search",
        user_id=current_user.id,
        ingredient_count=len(ingredients),
        result_count=total,
        page=page,
    )

    return jsonify({"results": page_results, "total": total, "has_more": has_more})


_VALID_FEEDBACK = {"yes_made", "not_for_me"}
_VALID_SKIP_REASONS = {"too_complex", "missing_key_ingredient", "not_my_taste"}
_RECIPE_IDS = {r["id"] for r in RECIPES}


@recipes_bp.route("/recipes/<recipe_id>")
@login_required
def detail(recipe_id: str):
    recipe_idx = _RECIPE_ID_TO_IDX.get(recipe_id)
    if recipe_idx is None:
        return "Recipe not found", 404

    recipe = RECIPES[recipe_idx]
    pantry_items = _get_pantry_items(current_user)
    user_ingredients = [item.standard_name or item.name for item in pantry_items]
    scored_recipe = score_recipe(recipe, recipe_idx, user_ingredients)

    if not scored_recipe:
        scored_recipe = recipe

    skipped_ids = [
        e.recipe_id
        for e in RecipeEngagement.query.filter_by(
            user_id=current_user.id, feedback="not_for_me"
        ).all()
    ]
    made_ids = [
        e.recipe_id
        for e in RecipeEngagement.query.filter_by(
            user_id=current_user.id, feedback="yes_made"
        ).all()
    ]

    return render_template(
        "recipes/detail.html",
        recipe=scored_recipe,
        skipped_ids=skipped_ids,
        made_ids=made_ids,
    )


@recipes_bp.route("/recipes/<recipe_id>/view", methods=["POST"])
@login_required
def track_view(recipe_id: str):
    if recipe_id not in _RECIPE_IDS:
        return jsonify({"error": "Recipe not found"}), 404

    existing = RecipeEngagement.query.filter_by(
        user_id=current_user.id, recipe_id=recipe_id
    ).first()

    if existing:
        existing.view_count += 1
        existing.engaged_at = datetime.now(timezone.utc)
    else:
        engagement = RecipeEngagement(
            user_id=current_user.id,
            recipe_id=recipe_id,
            view_count=1,
        )
        db.session.add(engagement)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Conflict"}), 409

    return jsonify({"ok": True})


@recipes_bp.route("/recipes/<recipe_id>/click", methods=["POST"])
@login_required
def track_click(recipe_id: str):
    if recipe_id not in _RECIPE_IDS:
        return jsonify({"error": "Recipe not found"}), 404

    existing = RecipeEngagement.query.filter_by(
        user_id=current_user.id, recipe_id=recipe_id
    ).first()

    if existing:
        existing.click_count = (existing.click_count or 0) + 1
        existing.engaged_at = datetime.now(timezone.utc)
    else:
        engagement = RecipeEngagement(
            user_id=current_user.id,
            recipe_id=recipe_id,
            click_count=1,
        )
        db.session.add(engagement)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Conflict"}), 409

    return jsonify({"ok": True})


@recipes_bp.route("/recipes/<recipe_id>/feedback", methods=["POST"])
@login_required
def feedback(recipe_id: str):
    if recipe_id not in _RECIPE_IDS:
        return jsonify({"error": "Recipe not found"}), 404

    data = request.get_json(silent=True) or {}
    fb = data.get("feedback")
    skip_reason = data.get("skip_reason")

    if fb not in _VALID_FEEDBACK:
        return jsonify({"error": "Invalid feedback value"}), 422
    if skip_reason is not None and skip_reason not in _VALID_SKIP_REASONS:
        return jsonify({"error": "Invalid skip_reason value"}), 422

    existing = RecipeEngagement.query.filter_by(
        user_id=current_user.id, recipe_id=recipe_id
    ).first()

    if existing:
        existing.feedback = fb
        existing.skip_reason = skip_reason if fb == "not_for_me" else None
        existing.engaged_at = datetime.now(timezone.utc)
    else:
        engagement = RecipeEngagement(
            user_id=current_user.id,
            recipe_id=recipe_id,
            feedback=fb,
            skip_reason=skip_reason if fb == "not_for_me" else None,
        )
        db.session.add(engagement)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Conflict"}), 409

    logger.info(
        "recipe_feedback",
        user_id=current_user.id,
        recipe_id=recipe_id,
        feedback=fb,
        skip_reason=skip_reason,
    )

    return jsonify({"ok": True})


@recipes_bp.route("/recipes/settings/expired-items", methods=["POST"])
@login_required
def update_expired_items_setting():
    data = request.get_json(silent=True) or {}
    days = data.get("days")

    if days is None or not isinstance(days, int):
        return jsonify({"error": "Invalid days value"}), 422
    if days < 0 or days > 90:
        return jsonify({"error": "Days must be between 0 and 90"}), 422

    current_user.expired_items_days = days
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Failed to update setting"}), 409

    logger.info(
        "update_expired_items_setting",
        user_id=current_user.id,
        days=days,
    )

    return jsonify({"ok": True, "days": days})


@recipes_bp.route("/recipes/pantry-items", methods=["GET"])
@login_required
def get_pantry_items():
    pantry_items = _get_pantry_items(current_user)
    items = [item.standard_name or item.name for item in pantry_items]
    return jsonify({"items": items})

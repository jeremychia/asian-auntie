from datetime import date, datetime, timezone

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Item, RecipeEngagement
from app.logging_config import get_logger
from app.recipes.data import RECIPES
from app.recipes.search import score_recipe

recipes_bp = Blueprint("recipes", __name__)
logger = get_logger(__name__)


@recipes_bp.route("/recipes")
@login_required
def index():
    today = date.today()
    pantry_items = (
        Item.query.filter_by(user_id=current_user.id)
        .filter(Item.removed_at.is_(None))
        .filter(Item.expiry_date >= today)
        .order_by(Item.name.asc())
        .all()
    )
    skipped_ids = [
        e.recipe_id
        for e in RecipeEngagement.query.filter_by(
            user_id=current_user.id, feedback="not_for_me"
        ).all()
    ]
    return render_template(
        "recipes/index.html",
        pantry_items=pantry_items,
        skipped_ids=skipped_ids,
    )


PAGE_SIZE = 10


@recipes_bp.route("/recipes/search", methods=["POST"])
@login_required
def search():
    data = request.get_json(silent=True) or {}
    ingredients: list[str] = [str(i).strip() for i in data.get("ingredients", []) if i]
    page: int = max(1, int(data.get("page", 1)))
    show_all: bool = bool(data.get("show_all", False))
    cuisine: str = str(data.get("cuisine", "")).strip()
    website: str = str(data.get("website", "")).strip()

    if not ingredients:
        return jsonify({"results": [], "total": 0, "has_more": False})

    results = []
    for recipe in RECIPES:
        # Apply cuisine filter
        if cuisine and recipe.get("cuisine", "") != cuisine:
            continue
        # Apply website filter
        if website and recipe.get("source", "") != website:
            continue

        scored = score_recipe(recipe, ingredients)
        if scored:
            results.append(scored)

    # Sort: match % descending, then fewer ingredients first (simpler recipes)
    results.sort(key=lambda r: (-r["match_pct"], r["total_count"]))

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

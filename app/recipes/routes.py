import re
from datetime import date

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app.models import Item
from app.logging_config import get_logger
from app.recipes.data import RECIPES

recipes_bp = Blueprint("recipes", __name__)
logger = get_logger(__name__)

# Words to ignore when matching ingredient names
_STOP_WORDS = {
    "a",
    "an",
    "the",
    "of",
    "with",
    "and",
    "or",
    "in",
    "for",
    "to",
    "sauce",
    "paste",
    "powder",
    "ground",
    "fresh",
    "dried",
    "sliced",
    "chopped",
    "whole",
    "boneless",
    "skinless",
    "raw",
}


def _words(text: str) -> set[str]:
    """Normalise an ingredient string into a set of meaningful words."""
    tokens = re.sub(r"[^a-z\s]", "", text.lower()).split()
    return {t for t in tokens if t not in _STOP_WORDS and len(t) > 1}


def _ingredient_matches(recipe_ingredient: str, user_ingredients: list[str]) -> bool:
    """Return True if any user ingredient shares at least one meaningful word."""
    ri_words = _words(recipe_ingredient)
    if not ri_words:
        return False
    for ui in user_ingredients:
        if ri_words & _words(ui):
            return True
    return False


def _score_recipe(recipe: dict, user_ingredients: list[str]) -> dict | None:
    """
    Compute match metadata for a recipe against the user's ingredient list.
    Returns None if 0 ingredients match.
    """
    matched, missing = [], []
    for ing in recipe["ingredients"]:
        if _ingredient_matches(ing, user_ingredients):
            matched.append(ing)
        else:
            missing.append(ing)

    total = len(recipe["ingredients"])
    if not matched:
        return None

    pct = round(len(matched) / total * 100)
    return {
        **recipe,
        "match_pct": pct,
        "matched_count": len(matched),
        "total_count": total,
        "matched": matched,
        "missing": missing,
    }


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
    return render_template(
        "recipes/index.html",
        pantry_items=pantry_items,
    )


@recipes_bp.route("/recipes/search", methods=["POST"])
@login_required
def search():
    data = request.get_json(silent=True) or {}
    ingredients: list[str] = [str(i).strip() for i in data.get("ingredients", []) if i]

    if not ingredients:
        return jsonify({"results": []})

    results = []
    for recipe in RECIPES:
        scored = _score_recipe(recipe, ingredients)
        if scored:
            results.append(scored)

    # Sort: match % descending, then fewer ingredients first (simpler recipes)
    results.sort(key=lambda r: (-r["match_pct"], r["total_count"]))
    results = results[:20]

    logger.info(
        "recipe_search",
        user_id=current_user.id,
        ingredient_count=len(ingredients),
        result_count=len(results),
    )

    return jsonify({"results": results})

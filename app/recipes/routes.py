import re
from datetime import date, datetime, timezone

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Item, RecipeEngagement
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

# Curated synonym map: user-typed alias → recipe ingredient term(s) it should match.
# Keep entries lowercase. Expand as zero-result searches are observed in the wild.
_SYNONYMS: dict[str, list[str]] = {
    # Fish sauce aliases
    "nam pla": ["fish sauce"],
    "patis": ["fish sauce"],
    # Soy sauce variants
    "light soy": ["light soy sauce"],
    "dark soy": ["dark soy sauce"],
    "sweet soy": ["sweet soy sauce"],
    "kecap manis": ["sweet soy sauce"],
    "kicap manis": ["sweet soy sauce"],
    # Shrimp paste aliases
    "blachan": ["belacan"],
    "blachan paste": ["belacan"],
    "trassi": ["belacan"],
    "shrimp paste": ["belacan"],
    "bagoong": ["belacan", "shrimp paste"],
    # Palm / coconut sugar aliases
    "gula melaka": ["palm sugar"],
    "coconut sugar": ["palm sugar"],
    "jaggery": ["palm sugar"],
    # Lemongrass
    "lemon grass": ["lemongrass"],
    "serai": ["lemongrass"],
    # Galangal
    "blue ginger": ["galangal"],
    "lengkuas": ["galangal"],
    # Kaffir lime leaves
    "makrut lime leaves": ["kaffir lime leaves"],
    "makrut lime": ["kaffir lime leaves"],
    "daun limau purut": ["kaffir lime leaves"],
    # Tamarind
    "tamarind paste": ["tamarind"],
    "tamarind juice": ["tamarind"],
    "asam": ["tamarind"],
    "asam jawa": ["tamarind"],
    # Coriander / cilantro
    "cilantro": ["coriander"],
    "coriander leaves": ["coriander"],
    # Spring onions
    "scallions": ["spring onions"],
    "green onions": ["spring onions"],
    # Bok choy
    "pak choi": ["bok choy"],
    "pak choy": ["bok choy"],
    "bak choi": ["bok choy"],
    # Chinese broccoli
    "gai lan": ["chinese broccoli"],
    "kailan": ["chinese broccoli"],
    "choy sum": ["chinese broccoli"],
    # Kangkung
    "water spinach": ["kangkung"],
    "morning glory": ["kangkung"],
    "water morning glory": ["kangkung"],
    # Doubanjiang
    "toban djan": ["doubanjiang"],
    "chilli bean paste": ["doubanjiang"],
    "bean paste": ["doubanjiang"],
    # Dried shrimp
    "dried prawns": ["dried shrimp"],
    # Generic protein expansions (singular → plural)
    "prawn": ["prawns"],
    "shrimp": ["prawns"],
    "egg": ["eggs"],
    # Oil aliases (map to generic "oil" so recipes still match)
    "vegetable oil": ["oil"],
    "cooking oil": ["oil"],
    "sunflower oil": ["oil"],
    "peanut oil": ["oil"],
    "canola oil": ["oil"],
    # Chilli variants
    "chili": ["chillies"],
    "chile": ["chillies"],
    "hot pepper": ["chillies"],
    "dried chili": ["dried chillies"],
    # Tofu aliases
    "beancurd": ["tofu"],
    "bean curd": ["tofu"],
    "tofu puff": ["tofu"],
    # Cornstarch
    "corn starch": ["cornstarch"],
    "corn flour": ["cornstarch"],
    # Tapioca
    "tapioca flour": ["tapioca starch"],
    # General flour
    "plain flour": ["flour"],
    "all purpose flour": ["flour"],
}


def _words(text: str) -> set[str]:
    """Normalise an ingredient string into a set of meaningful words."""
    tokens = re.sub(r"[^a-z\s]", "", text.lower()).split()
    return {t for t in tokens if t not in _STOP_WORDS and len(t) > 1}


def _ingredient_matches(recipe_ingredient: str, user_ingredients: list[str]) -> bool:
    """Return True if any user ingredient (or its known synonyms) matches the recipe ingredient."""
    ri_words = _words(recipe_ingredient)
    if not ri_words:
        return False
    for ui in user_ingredients:
        # Direct word overlap
        if ri_words & _words(ui):
            return True
        # Synonym expansion: check canonical forms the user alias maps to
        for canonical in _SYNONYMS.get(ui.lower().strip(), []):
            if ri_words & _words(canonical):
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

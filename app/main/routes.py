from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import current_user

from app.recipes.data import RECIPES
from app.recipes.search import score_recipe
from app.perishables.forms import PANTRY_ITEMS as _PANTRY_ITEMS_VOCAB

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("perishables.dashboard"))
    return render_template("landing.html", pantry_vocab=_PANTRY_ITEMS_VOCAB)


@main_bp.route("/search")
def search():
    raw = request.args.get("ingredients", "")
    ingredients = [i.strip() for i in raw.split(",") if i.strip()]
    if not ingredients:
        return jsonify({"results": []})

    results = []
    for idx, recipe in enumerate(RECIPES):
        scored = score_recipe(recipe, idx, ingredients)
        if scored:
            results.append(scored)

    results.sort(key=lambda r: (-r["match_pct"], r["total_count"]))
    return jsonify({"results": results[:12]})

"""Tests for recipes routes and search logic."""

from datetime import date, timedelta

import pytest

from app.models import Item
from app.recipes.search import score_recipe, parse_cook_time, candidate_recipe_indices
from app.recipes.data import RECIPES


def future_date(days=30):
    return date.today() + timedelta(days=days)


@pytest.fixture
def pantry_items(db, user):
    from app.extensions import db as _db

    items = [
        Item(
            user_id=user.id,
            name="Coconut Milk",
            standard_name="Coconut milk",
            item_type="other",
            expiry_date=future_date(60),
        ),
        Item(
            user_id=user.id,
            name="Fish Sauce",
            standard_name="Fish sauce",
            item_type="condiment",
            expiry_date=future_date(90),
        ),
    ]
    db.session.add_all(items)
    db.session.commit()
    ids = [i.id for i in items]
    yield items
    for item_id in ids:
        fresh = _db.session.get(Item, item_id)
        if fresh:
            db.session.delete(fresh)
    db.session.commit()


def test_recipes_page_loads(auth_client):
    r = auth_client.get("/recipes")
    assert r.status_code == 200


def test_recipes_search_returns_results(auth_client, pantry_items):
    r = auth_client.post(
        "/recipes/search",
        json={"ingredients": ["Coconut milk", "Fish sauce"], "page": 1},
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert "results" in data
    assert "total" in data


def test_recipes_search_empty_ingredients_returns_empty(auth_client):
    r = auth_client.post(
        "/recipes/search",
        json={"ingredients": [], "page": 1},
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["results"] == []
    assert data["total"] == 0


def test_recipe_detail_valid(auth_client):
    if not RECIPES:
        pytest.skip("No recipes in data")
    recipe_id = RECIPES[0]["id"]
    r = auth_client.get(f"/recipes/{recipe_id}")
    assert r.status_code == 200


def test_recipe_detail_invalid(auth_client):
    r = auth_client.get("/recipes/nonexistent-recipe-id-xyz")
    assert r.status_code == 404


def test_recipe_feedback(auth_client):
    if not RECIPES:
        pytest.skip("No recipes in data")
    recipe_id = RECIPES[0]["id"]
    r = auth_client.post(
        f"/recipes/{recipe_id}/feedback",
        json={"feedback": "not_for_me"},
        content_type="application/json",
    )
    assert r.status_code == 200
    assert r.get_json().get("ok") is True


def test_recipe_feedback_invalid(auth_client):
    if not RECIPES:
        pytest.skip("No recipes in data")
    recipe_id = RECIPES[0]["id"]
    r = auth_client.post(
        f"/recipes/{recipe_id}/feedback",
        json={"feedback": "bogus_value"},
        content_type="application/json",
    )
    assert r.status_code == 422


def test_recipe_track_view(auth_client):
    if not RECIPES:
        pytest.skip("No recipes in data")
    recipe_id = RECIPES[0]["id"]
    r = auth_client.post(f"/recipes/{recipe_id}/view")
    assert r.status_code in (200, 201, 204)


def test_parse_cook_time_minutes():
    assert parse_cook_time("30 min") == 30


def test_parse_cook_time_hours_and_minutes():
    assert parse_cook_time("1 hour 30 min") == 90


def test_parse_cook_time_hours_only():
    assert parse_cook_time("2 hours") == 120


def test_parse_cook_time_invalid():
    assert parse_cook_time("quick") is None
    assert parse_cook_time("") is None
    assert parse_cook_time(None) is None


def test_candidate_recipe_indices_returns_set():
    result = candidate_recipe_indices(["coconut milk", "fish sauce"])
    assert isinstance(result, set)


def test_score_recipe_structure():
    if not RECIPES:
        pytest.skip("No recipes in data")
    recipe = RECIPES[0]
    result = score_recipe(recipe, 0, ["coconut milk"])
    # score_recipe returns None or a dict
    assert result is None or isinstance(result, dict)


def test_recipes_page_requires_login(auth_client):
    # Log out, then verify the recipes page requires a session
    auth_client.post("/logout", follow_redirects=False)
    r = auth_client.get("/recipes", follow_redirects=False)
    assert r.status_code in (302, 401)


def test_update_expired_items_setting(auth_client):
    r = auth_client.post(
        "/recipes/settings/expired-items",
        json={"days": 3},
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data.get("ok") is True


def test_update_expired_items_setting_invalid(auth_client):
    r = auth_client.post(
        "/recipes/settings/expired-items",
        json={"days": -1},
        content_type="application/json",
    )
    assert r.status_code == 422


def test_get_pantry_items_endpoint(auth_client):
    r = auth_client.get("/recipes/pantry-items")
    assert r.status_code == 200
    data = r.get_json()
    assert "items" in data
    assert isinstance(data["items"], list)


# ── score_recipe with normalized_ingredients ──────────────────────────────────

_HAKKA_RECIPE = {
    "id": "hakka-yellow-wine-chicken-test",
    "name": "Hakka yellow wine chicken",
    "source": "Spice N Pans",
    "source_url": "https://www.youtube.com/watch?v=test",
    "cuisine": "Chinese",
    "cook_time": "unknown",
    "difficulty": "Medium",
    "ingredients": [
        "old ginger, grated",
        "sesame oil",
        "chicken, cut into bite-sized pieces",
        "enough water to cover the chicken",
        "hakka glutinous rice wine",
        "salt",
    ],
    "normalized_ingredients": [
        "Ginger",
        "Sesame oil",
        "Chicken",
        "Rice wine",
    ],
}


@pytest.fixture
def patched_recipes(monkeypatch):
    """Insert a controlled test recipe into the search index."""
    import app.recipes.search as search_mod

    idx = len(search_mod._RECIPE_INGREDIENTS)
    search_mod._RECIPE_ID_TO_IDX[_HAKKA_RECIPE["id"]] = idx

    from app.recipes.search import _words

    ing_data = []
    for norm in _HAKKA_RECIPE["normalized_ingredients"]:
        norm_lower = norm.lower().strip()
        words = _words(norm_lower)
        ing_data.append((norm, norm_lower, words))
        search_mod._INGREDIENT_INDEX[norm_lower].add(idx)
        for word in words:
            search_mod._INGREDIENT_INDEX[word].add(idx)
    search_mod._RECIPE_INGREDIENTS.append(ing_data)

    yield idx

    search_mod._RECIPE_INGREDIENTS.pop()
    del search_mod._RECIPE_ID_TO_IDX[_HAKKA_RECIPE["id"]]


def test_score_recipe_normalized_partial_match(patched_recipes):
    """When user has 3 of 4 normalized ingredients, match_pct is 75% and
    matched/missing use normalized names, not raw ingredient strings."""
    idx = patched_recipes
    result = score_recipe(_HAKKA_RECIPE, idx, ["Ginger", "Sesame oil", "Chicken"])

    assert result is not None
    assert result["match_pct"] == 75
    assert result["matched_count"] == 3
    assert result["total_count"] == 4
    assert set(result["matched"]) == {"Ginger", "Sesame oil", "Chicken"}
    assert result["missing"] == ["Rice wine"]


def test_score_recipe_normalized_full_match(patched_recipes):
    """When user has all normalized ingredients, match_pct is 100%."""
    idx = patched_recipes
    result = score_recipe(
        _HAKKA_RECIPE, idx, ["Ginger", "Sesame oil", "Chicken", "Rice wine"]
    )

    assert result is not None
    assert result["match_pct"] == 100
    assert result["missing"] == []


def test_score_recipe_normalized_no_match(patched_recipes):
    """When user has none of the ingredients, score_recipe returns None."""
    idx = patched_recipes
    result = score_recipe(_HAKKA_RECIPE, idx, ["Coconut milk", "Fish sauce"])

    assert result is None


def test_recipes_search_title_filter_match(auth_client, pantry_items):
    first_name = RECIPES[0]["name"]
    r = auth_client.post(
        "/recipes/search",
        json={
            "ingredients": ["Coconut milk", "Fish sauce"],
            "page": 1,
            "title": first_name[:5],
        },
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    for recipe in data["results"]:
        assert first_name[:5].lower() in recipe["name"].lower()


def test_recipes_search_title_filter_no_match(auth_client, pantry_items):
    r = auth_client.post(
        "/recipes/search",
        json={
            "ingredients": ["Coconut milk", "Fish sauce"],
            "page": 1,
            "title": "zzz_nonexistent_recipe_zzz",
        },
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["results"] == []
    assert data["total"] == 0


def test_recipes_search_title_filter_includes_zero_match_recipes(
    auth_client, pantry_items
):
    # "Egg Drop Soup" uses chicken stock/bouillon, not chicken meat — score_recipe
    # returns None for ["Chicken"], but the title filter should still surface it at 0%.
    r = auth_client.post(
        "/recipes/search",
        json={"ingredients": ["Chicken"], "page": 1, "title": "egg drop soup"},
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert (
        data["total"] > 0
    ), "Expected egg drop soup results even with 0% ingredient match"
    zero_match = [rec for rec in data["results"] if rec["match_pct"] == 0]
    assert zero_match, "Expected at least one 0% match result"
    assert all("egg drop soup" in rec["name"].lower() for rec in data["results"])


def test_recipes_search_title_filter_case_insensitive(auth_client, pantry_items):
    first_name = RECIPES[0]["name"]
    fragment = first_name[:5]
    r_lower = auth_client.post(
        "/recipes/search",
        json={
            "ingredients": ["Coconut milk", "Fish sauce"],
            "page": 1,
            "title": fragment.lower(),
        },
        content_type="application/json",
    )
    r_upper = auth_client.post(
        "/recipes/search",
        json={
            "ingredients": ["Coconut milk", "Fish sauce"],
            "page": 1,
            "title": fragment.upper(),
        },
        content_type="application/json",
    )
    assert r_lower.status_code == 200
    assert r_upper.status_code == 200
    assert r_lower.get_json()["total"] == r_upper.get_json()["total"]


def test_score_recipe_matched_are_normalized_names_not_raw(patched_recipes):
    """matched list must contain normalized names, never raw ingredient strings."""
    idx = patched_recipes
    result = score_recipe(_HAKKA_RECIPE, idx, ["Sesame oil"])

    assert result is not None
    assert "Sesame oil" in result["matched"]
    assert "sesame oil" not in result["matched"]
    assert not any("old ginger" in m for m in result["matched"])
    assert not any("cut into" in m for m in result["matched"])

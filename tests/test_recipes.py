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

"""Tests for the JWT REST API (/api/v1/...)."""

from datetime import date, timedelta

import pytest

from app.models import User, Item


def future_date(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


@pytest.fixture
def api_user(db):
    from app.extensions import bcrypt
    from app.models import RefreshToken

    u = User(
        username="api_testuser",
        password_hash=bcrypt.generate_password_hash("apipass123").decode(),
        onboarding_done=True,
    )
    db.session.add(u)
    db.session.commit()
    yield u
    RefreshToken.query.filter_by(user_id=u.id).delete()
    Item.query.filter_by(user_id=u.id).delete()
    db.session.delete(u)
    db.session.commit()


@pytest.fixture
def tokens(client, api_user):
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "api_testuser", "password": "apipass123"},
    )
    assert r.status_code == 200
    data = r.get_json()
    return data["access_token"], data["refresh_token"]


@pytest.fixture
def access_token(tokens):
    return tokens[0]


@pytest.fixture
def refresh_token(tokens):
    return tokens[1]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# --- Auth endpoints ---


def test_api_register(client, db):
    r = client.post(
        "/api/v1/auth/register",
        json={"username": "brand_new_user", "password": "brandpass123"},
    )
    assert r.status_code == 201
    assert "user_id" in r.get_json()
    User.query.filter_by(username="brand_new_user").delete()
    db.session.commit()


def test_api_register_duplicate_username(client, api_user):
    r = client.post(
        "/api/v1/auth/register",
        json={"username": "api_testuser", "password": "apipass123"},
    )
    assert r.status_code == 409


def test_api_login_success(client, api_user):
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "api_testuser", "password": "apipass123"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_api_login_wrong_password(client, api_user):
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "api_testuser", "password": "wrongpass"},
    )
    assert r.status_code == 401


def test_api_token_refresh(client, tokens):
    _, refresh = tokens
    r = client.post(
        "/api/v1/auth/refresh",
        headers=auth_headers(refresh),
    )
    assert r.status_code == 200
    data = r.get_json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_api_logout(client, tokens):
    _, refresh = tokens
    r = client.post("/api/v1/auth/logout", headers=auth_headers(refresh))
    assert r.status_code == 200

    # Refresh token should now be invalid
    r2 = client.post("/api/v1/auth/refresh", headers=auth_headers(refresh))
    assert r2.status_code == 401


# --- Items endpoints ---


def test_api_list_items_empty(client, access_token):
    r = client.get("/api/v1/items", headers=auth_headers(access_token))
    assert r.status_code == 200
    data = r.get_json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_api_create_item(client, db, access_token, api_user):
    r = client.post(
        "/api/v1/items",
        json={
            "name": "Oyster Sauce",
            "expiry_date": future_date(60),
            "item_type": "sauce",
        },
        headers=auth_headers(access_token),
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["name"] == "Oyster Sauce"
    item_id = data["id"]

    Item.query.filter_by(id=item_id).delete()
    db.session.commit()


def test_api_create_item_past_expiry(client, access_token):
    past = (date.today() - timedelta(days=1)).isoformat()
    r = client.post(
        "/api/v1/items",
        json={"name": "Old Item", "expiry_date": past, "item_type": "other"},
        headers=auth_headers(access_token),
    )
    assert r.status_code == 422


def test_api_create_item_missing_fields(client, access_token):
    r = client.post(
        "/api/v1/items",
        json={"name": "No Expiry"},
        headers=auth_headers(access_token),
    )
    assert r.status_code == 422


def test_api_get_item(client, db, access_token, api_user):
    item = Item(
        user_id=api_user.id,
        name="Test Item",
        item_type="other",
        expiry_date=date.today() + timedelta(days=30),
    )
    db.session.add(item)
    db.session.commit()

    r = client.get(f"/api/v1/items/{item.id}", headers=auth_headers(access_token))
    assert r.status_code == 200
    assert r.get_json()["name"] == "Test Item"

    db.session.delete(item)
    db.session.commit()


def test_api_update_item(client, db, access_token, api_user):
    item = Item(
        user_id=api_user.id,
        name="Original Name",
        item_type="other",
        expiry_date=date.today() + timedelta(days=30),
    )
    db.session.add(item)
    db.session.commit()

    r = client.patch(
        f"/api/v1/items/{item.id}",
        json={"name": "Updated Name"},
        headers=auth_headers(access_token),
    )
    assert r.status_code == 200
    assert r.get_json()["name"] == "Updated Name"

    db.session.delete(item)
    db.session.commit()


def test_api_delete_item(client, db, access_token, api_user):
    item = Item(
        user_id=api_user.id,
        name="To Delete",
        item_type="other",
        expiry_date=date.today() + timedelta(days=10),
    )
    db.session.add(item)
    db.session.commit()
    item_id = item.id

    r = client.delete(f"/api/v1/items/{item_id}", headers=auth_headers(access_token))
    assert r.status_code in (200, 204)

    # Delete is a soft delete — item still exists but removed_at is set
    from app.extensions import db as _db

    deleted = _db.session.get(Item, item_id)
    assert deleted is not None
    assert deleted.removed_at is not None
    _db.session.delete(deleted)
    _db.session.commit()


def test_api_requires_auth(client):
    r = client.get("/api/v1/items")
    assert r.status_code == 401


def test_api_cannot_access_other_users_item(client, db, access_token, api_user):
    from app.extensions import bcrypt

    other = User(
        username="other_api_user",
        password_hash=bcrypt.generate_password_hash("pass12345").decode(),
        onboarding_done=True,
    )
    db.session.add(other)
    db.session.commit()

    item = Item(
        user_id=other.id,
        name="Private Item",
        item_type="other",
        expiry_date=date.today() + timedelta(days=10),
    )
    db.session.add(item)
    db.session.commit()

    r = client.get(f"/api/v1/items/{item.id}", headers=auth_headers(access_token))
    assert r.status_code in (403, 404)

    db.session.delete(item)
    db.session.delete(other)
    db.session.commit()

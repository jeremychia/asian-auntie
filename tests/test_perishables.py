"""Tests for perishables (pantry) routes: dashboard, add, edit, remove items."""

from datetime import date, timedelta

import pytest

from app.models import Item
from app.extensions import db as _db


@pytest.fixture
def group_items(db, user):
    """Two items sharing the same standard_name (a group) in the pantry."""
    items = [
        Item(
            user_id=user.id,
            name="Soy Sauce",
            standard_name="Light soy sauce",
            item_type="condiment",
            expiry_date=date.today() + timedelta(days=30),
            location="pantry",
        ),
        Item(
            user_id=user.id,
            name="Soy Sauce",
            standard_name="Light soy sauce",
            item_type="condiment",
            expiry_date=date.today() + timedelta(days=60),
            location="pantry",
        ),
    ]
    db.session.add_all(items)
    db.session.commit()
    yield items
    for i in items:
        fresh = _db.session.get(Item, i.id)
        if fresh:
            db.session.delete(fresh)
    db.session.commit()


def future_date(days=30):
    return (date.today() + timedelta(days=days)).isoformat()


@pytest.fixture
def item(db, user):
    i = Item(
        user_id=user.id,
        name="Soy Sauce",
        standard_name="Light soy sauce",
        item_type="condiment",
        expiry_date=date.today() + timedelta(days=30),
        location="pantry",
    )
    db.session.add(i)
    db.session.commit()
    yield i
    refreshed = _db.session.get(Item, i.id)
    if refreshed:
        db.session.delete(refreshed)
        db.session.commit()


def test_dashboard_loads(auth_client):
    r = auth_client.get("/dashboard")
    assert r.status_code == 200


def test_dashboard_shows_item(auth_client, item):
    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert b"Soy Sauce" in r.data


def test_add_item_page_loads(auth_client):
    r = auth_client.get("/items/add")
    assert r.status_code == 200


def test_add_item_manual(auth_client, db, user):
    r = auth_client.post(
        "/items/add",
        data={
            "step": "confirm",
            "name": "Fish Sauce",
            "standard_name": "Fish sauce",
            "item_type": "condiment",
            "expiry_date": future_date(60),
            "location": "pantry",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    created = Item.query.filter_by(user_id=user.id, name="Fish Sauce").first()
    assert created is not None
    db.session.delete(created)
    db.session.commit()


def test_item_detail_loads(auth_client, item):
    r = auth_client.get(f"/items/{item.id}")
    assert r.status_code == 200
    assert b"Soy Sauce" in r.data


def test_item_detail_requires_login(auth_client, item):
    # Log out, then verify the item detail requires a session
    auth_client.post("/logout", follow_redirects=False)
    r = auth_client.get(f"/items/{item.id}", follow_redirects=False)
    assert r.status_code == 302


def test_item_ownership_enforced_via_api(client, db, item):
    # Create a second user and verify they cannot access the item via the API
    from app.models import User, RefreshToken
    from app.extensions import bcrypt

    other = User(
        username="otherapiuser",
        password_hash=bcrypt.generate_password_hash("apipass123").decode(),
        onboarding_done=True,
    )
    db.session.add(other)
    db.session.commit()

    r_login = client.post(
        "/api/v1/auth/login",
        json={"username": "otherapiuser", "password": "apipass123"},
    )
    assert r_login.status_code == 200
    token = r_login.get_json()["access_token"]

    r = client.get(
        f"/api/v1/items/{item.id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code in (403, 404)

    RefreshToken.query.filter_by(user_id=other.id).delete()
    db.session.delete(other)
    db.session.commit()


def test_mark_item_used(auth_client, db, user, item):
    r = auth_client.post(f"/items/{item.id}/use", follow_redirects=True)
    assert r.status_code == 200
    db.session.refresh(item)
    assert item.removed_at is not None
    assert item.removal_reason == "used"


def test_remove_item(auth_client, db, item):
    r = auth_client.post(
        f"/items/{item.id}/remove",
        data={"reason": "discarded"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    db.session.refresh(item)
    assert item.removed_at is not None


def test_update_item_location(auth_client, db, item):
    r = auth_client.post(
        f"/items/{item.id}/location",
        data={"location": "fridge"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    db.session.refresh(item)
    assert item.location == "fridge"


def test_update_item_type(auth_client, db, item):
    r = auth_client.post(
        f"/items/{item.id}/type",
        data={"item_type": "sauce"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    db.session.refresh(item)
    assert item.item_type == "sauce"


def test_edit_item_page_loads(auth_client, item):
    r = auth_client.get(f"/items/{item.id}/edit")
    assert r.status_code == 200


def test_update_item_name_and_expiry(auth_client, db, item):
    new_expiry = future_date(90)
    r = auth_client.post(
        f"/items/{item.id}/edit",
        data={
            "name": "Dark Soy Sauce",
            "expiry_date": new_expiry,
            "item_type": "condiment",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    db.session.refresh(item)
    assert item.name == "Dark Soy Sauce"


def test_remove_expired_items(auth_client, db, user):
    expired = Item(
        user_id=user.id,
        name="Old Sauce",
        item_type="sauce",
        expiry_date=date.today() - timedelta(days=5),
        location="pantry",
    )
    db.session.add(expired)
    db.session.commit()
    expired_id = expired.id

    r = auth_client.post("/items/remove-expired", follow_redirects=True)
    assert r.status_code == 200

    refreshed = _db.session.get(Item, expired_id)
    assert refreshed is not None
    assert refreshed.removed_at is not None
    db.session.delete(refreshed)
    db.session.commit()


def test_audit_page_loads(auth_client):
    r = auth_client.get("/audit")
    assert r.status_code == 200


def test_barcode_confirm_renders_off_image_url(auth_client):
    # OFF image URL should appear in the confirm step img tag
    off_url = "https://images.openfoodfacts.org/images/products/123/test.jpg"
    r = auth_client.post(
        "/items/add",
        data={
            "step": "barcode_confirm",
            "name": "Test Product",
            "item_type": "other",
            "shelf_life_days": "90",
            "off_image_path": off_url,
            "barcode": "12345678",
        },
    )
    assert r.status_code == 200
    assert off_url.encode() in r.data


def test_barcode_confirm_no_image_when_off_image_path_empty(auth_client):
    # No photo section when off_image_path is absent
    r = auth_client.post(
        "/items/add",
        data={
            "step": "barcode_confirm",
            "name": "No Image Product",
            "item_type": "other",
            "shelf_life_days": "90",
            "off_image_path": "",
            "barcode": "12345678",
        },
    )
    assert r.status_code == 200
    assert b"add-review-photo" not in r.data


def test_csp_allows_off_image_hosts(auth_client):
    r = auth_client.get("/dashboard")
    csp = r.headers.get("Content-Security-Policy", "")
    assert "images.openfoodfacts.org" in csp


def test_add_item_uses_user_custom_locations(auth_client, db, user):
    import json
    from app.models import User as _User

    # auth_client's login request causes session.remove(), detaching the user
    # fixture object. Re-query to get a session-attached instance before modifying.
    live = db.session.get(_User, user.id)
    live.custom_locations = json.dumps(["Spice Rack", "Basement Freezer"])
    db.session.commit()

    r = auth_client.get("/items/add?skip=1")
    assert r.status_code == 200
    assert b"Spice Rack" in r.data
    assert b"Basement Freezer" in r.data

    live.custom_locations = None
    db.session.commit()


def test_add_item_confirm_uses_user_custom_locations(auth_client, db, user):
    import json
    from app.models import User as _User

    live = db.session.get(_User, user.id)
    live.custom_locations = json.dumps(["Wine Cellar", "Counter"])
    db.session.commit()

    r = auth_client.post(
        "/items/add",
        data={
            "step": "barcode_confirm",
            "name": "Test Wine",
            "item_type": "other",
            "shelf_life_days": "365",
            "barcode": "12345678",
        },
    )
    assert r.status_code == 200
    assert b"Wine Cellar" in r.data

    live.custom_locations = None
    db.session.commit()


@pytest.fixture
def item_group(db, user):
    """Two items with the same standard_name, sorted by expiry (soonest first)."""
    items = [
        Item(
            user_id=user.id,
            name="Coconut Milk A",
            standard_name="Coconut milk",
            item_type="other",
            expiry_date=date.today() + timedelta(days=10),
        ),
        Item(
            user_id=user.id,
            name="Coconut Milk B",
            standard_name="Coconut milk",
            item_type="other",
            expiry_date=date.today() + timedelta(days=30),
        ),
    ]
    db.session.add_all(items)
    db.session.commit()
    yield items
    for i in items:
        refreshed = _db.session.get(Item, i.id)
        if refreshed:
            db.session.delete(refreshed)
    db.session.commit()


def test_group_detail_loads(auth_client, item_group):
    r = auth_client.get("/items/group/Coconut milk")
    assert r.status_code == 200
    assert b"Coconut milk" in r.data


def test_group_detail_reserve_has_quantity_selector(auth_client, item_group):
    r = auth_client.get("/items/group/Coconut milk")
    assert r.status_code == 200
    # The "How much is left?" section must appear in the action sheets
    assert b"How much is left?" in r.data
    # All four quantity options must be present
    for val in [b"full", b"three_quarters", b"half", b"nearly_gone"]:
        assert val in r.data


def test_group_detail_quantity_state_update(auth_client, db, item_group):
    reserve = item_group[1]
    r = auth_client.post(
        f"/items/{reserve.id}/quantity",
        data={"quantity_state": "half", "next": "/items/group/Coconut milk"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    db.session.refresh(reserve)
    assert reserve.quantity_state == "half"


def test_bulk_action_mark_used(auth_client, db, user):
    items = [
        Item(
            user_id=user.id,
            name=f"Bulk Item {i}",
            item_type="other",
            expiry_date=date.today() + timedelta(days=10),
        )
        for i in range(2)
    ]
    db.session.add_all(items)
    db.session.commit()
    item_ids = [i.id for i in items]

    r = auth_client.post(
        "/items/bulk-action",
        data={"action": "used", "item_ids": [str(i) for i in item_ids]},
        follow_redirects=True,
    )
    assert r.status_code == 200
    for item_id in item_ids:
        refreshed = _db.session.get(Item, item_id)
        if refreshed:
            assert refreshed.removed_at is not None
            db.session.delete(refreshed)
    db.session.commit()


def test_dashboard_by_location_groups_items(auth_client, db, user):
    fridge_item = Item(
        user_id=user.id,
        name="Oat Milk",
        item_type="dairy",
        expiry_date=date.today() + timedelta(days=5),
        location="fridge",
    )
    pantry_item = Item(
        user_id=user.id,
        name="Fish Sauce",
        item_type="sauce",
        expiry_date=date.today() + timedelta(days=60),
        location="pantry",
    )
    db.session.add_all([fridge_item, pantry_item])
    db.session.commit()

    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert b"Fridge" in r.data
    assert b"Pantry" in r.data
    assert b"Oat Milk" in r.data
    assert b"Fish Sauce" in r.data

    db.session.delete(fridge_item)
    db.session.delete(pantry_item)
    db.session.commit()


def test_dashboard_expired_banner_shown(auth_client, db, user):
    expired_item = Item(
        user_id=user.id,
        name="Old Kewpie",
        item_type="condiment",
        expiry_date=date.today() - timedelta(days=3),
        location="fridge",
    )
    db.session.add(expired_item)
    db.session.commit()

    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert b"expired" in r.data
    assert b"Old Kewpie" in r.data

    db.session.delete(expired_item)
    db.session.commit()


def test_dashboard_no_location_goes_to_other(auth_client, db, user):
    unlabelled_item = Item(
        user_id=user.id,
        name="Mystery Paste",
        item_type="other",
        expiry_date=date.today() + timedelta(days=20),
        location=None,
    )
    db.session.add(unlabelled_item)
    db.session.commit()

    r = auth_client.get("/dashboard")
    assert r.status_code == 200
    assert b"Mystery Paste" in r.data
    assert b"Other" in r.data

    db.session.delete(unlabelled_item)
    db.session.commit()


def test_dashboard_kanban_columns_equal_class(auth_client, db, user):
    """Every rendered kanban column uses the same CSS class so CSS can enforce equal widths."""
    import re

    items = [
        Item(
            user_id=user.id,
            name="Oat Milk",
            item_type="dairy",
            expiry_date=date.today() + timedelta(days=5),
            location="fridge",
        ),
        Item(
            user_id=user.id,
            name="Fish Sauce",
            item_type="sauce",
            expiry_date=date.today() + timedelta(days=30),
            location="pantry",
        ),
        Item(
            user_id=user.id,
            name="Frozen Peas",
            item_type="other",
            expiry_date=date.today() + timedelta(days=90),
            location="freezer",
        ),
    ]
    db.session.add_all(items)
    db.session.commit()

    r = auth_client.get("/dashboard")
    assert r.status_code == 200

    html = r.data.decode()
    # Each column is an opening div with class="kanban__col"; count them
    cols = re.findall(r'<div\s+class="kanban__col"', html)
    assert len(cols) == 3, f"Expected 3 equal-width columns, found {len(cols)}"
    # All must use exactly "kanban__col" — no per-column variant class that would break equal widths
    variant_cols = re.findall(r'<div\s+class="kanban__col\s+[^"]+"', html)
    assert len(variant_cols) == 0, "Columns must not have per-column variant classes"

    for item in items:
        db.session.delete(item)
    db.session.commit()


# ── move_group ────────────────────────────────────────────────────────────────


def test_move_group_single_item(auth_client, db, item):
    r = auth_client.post(
        "/items/move-group",
        json={"item_ids": [item.id], "location": "fridge"},
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is True
    db.session.refresh(item)
    assert item.location == "fridge"


def test_move_group_moves_all_items(auth_client, db, group_items):
    ids = [i.id for i in group_items]
    r = auth_client.post(
        "/items/move-group",
        json={"item_ids": ids, "location": "freezer"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert data["moved"] == 2
    for i in group_items:
        db.session.refresh(i)
        assert i.location == "freezer"


def test_move_group_rejects_other_users_items(client, db, item, user):
    from app.models import User
    from app.extensions import bcrypt

    other = User(
        username="other_move_user",
        password_hash=bcrypt.generate_password_hash("pass123").decode(),
        onboarding_done=True,
    )
    db.session.add(other)
    db.session.commit()

    client.post(
        "/login",
        data={"username": "other_move_user", "password": "pass123"},
        follow_redirects=True,
    )
    r = client.post(
        "/items/move-group",
        json={"item_ids": [item.id], "location": "fridge"},
    )
    assert r.status_code == 404

    db.session.delete(other)
    db.session.commit()


def test_move_group_rejects_empty_ids(auth_client):
    r = auth_client.post(
        "/items/move-group",
        json={"item_ids": [], "location": "fridge"},
    )
    assert r.status_code == 400


def test_move_group_rejects_missing_ids(auth_client):
    r = auth_client.post(
        "/items/move-group",
        json={"location": "fridge"},
    )
    assert r.status_code == 400


def test_move_group_rejects_long_location(auth_client, item):
    r = auth_client.post(
        "/items/move-group",
        json={"item_ids": [item.id], "location": "x" * 33},
    )
    assert r.status_code == 400


def test_move_group_requires_login(client, item):
    r = client.post(
        "/items/move-group",
        json={"item_ids": [item.id], "location": "fridge"},
    )
    assert r.status_code in (302, 401)

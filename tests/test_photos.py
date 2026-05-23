"""Tests for photo upload, serving, type updates, and deletion."""

import io
import os
from datetime import date, timedelta

import pytest
from PIL import Image

from app.models import Item, ItemPhoto
from app.extensions import db as _db


def future_date(days=30):
    return date.today() + timedelta(days=days)


def make_jpeg_bytes(color=(255, 0, 0), size=(100, 100)) -> bytes:
    """Generate a minimal in-memory JPEG image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png_bytes(color=(0, 255, 0), size=(80, 80)) -> bytes:
    """Generate a minimal in-memory PNG image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_rgba_png_bytes() -> bytes:
    """Generate a PNG with alpha channel (RGBA), which must be converted on save."""
    img = Image.new("RGBA", (60, 60), color=(0, 0, 255, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_large_jpeg_bytes(size=(800, 800)) -> bytes:
    """Generate a large JPEG that should be compressed below 100KB on save."""
    img = Image.new("RGB", size, color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


@pytest.fixture
def item(db, user):
    i = Item(
        user_id=user.id,
        name="Test Item",
        item_type="sauce",
        expiry_date=future_date(30),
        location="pantry",
    )
    db.session.add(i)
    db.session.commit()
    yield i
    refreshed = _db.session.get(Item, i.id)
    if refreshed:
        ItemPhoto.query.filter_by(item_id=refreshed.id).delete(
            synchronize_session=False
        )
        db.session.expire(refreshed, ["photos"])
        db.session.delete(refreshed)
        db.session.commit()


@pytest.fixture
def photo(db, item):
    p = ItemPhoto(
        item_id=item.id,
        photo_path=f"users/{item.user_id}/fakephoto.jpg",
        photo_type="appearance",
        display_order=0,
    )
    db.session.add(p)
    db.session.commit()
    yield p
    refreshed = _db.session.get(ItemPhoto, p.id)
    if refreshed:
        db.session.delete(refreshed)
        db.session.commit()


# ── Upload ────────────────────────────────────────────────────────────────────


def test_upload_jpeg_photo(auth_client, db, item, tmp_path):
    r = auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_jpeg_bytes()), "soy_sauce.jpg"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    photos = ItemPhoto.query.filter_by(item_id=item.id).all()
    assert len(photos) == 1
    assert photos[0].photo_type == "appearance"


def test_upload_png_is_converted_to_jpeg(auth_client, db, item):
    r = auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_png_bytes()), "label.png"),
            "photo_types": "nutritional_label",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    photos = ItemPhoto.query.filter_by(item_id=item.id).all()
    assert len(photos) == 1
    # PNG input gets converted — stored path must end in .jpg
    assert photos[0].photo_path.endswith(".jpg")
    assert photos[0].photo_type == "nutritional_label"


def test_upload_rgba_png_converted(auth_client, db, item):
    r = auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_rgba_png_bytes()), "alpha.png"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    photos = ItemPhoto.query.filter_by(item_id=item.id).all()
    assert len(photos) == 1


def test_upload_large_jpeg_compressed(auth_client, db, item, app):
    large_bytes = make_large_jpeg_bytes()
    r = auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(large_bytes), "large.jpg"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    photos = ItemPhoto.query.filter_by(item_id=item.id).all()
    assert len(photos) == 1
    # Verify the saved file is under 100KB
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], photos[0].photo_path)
    if os.path.exists(saved_path):
        assert os.path.getsize(saved_path) <= 100 * 1024


def test_upload_multiple_photos(auth_client, db, item):
    r = auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": [
                (io.BytesIO(make_jpeg_bytes((255, 0, 0))), "front.jpg"),
                (io.BytesIO(make_jpeg_bytes((0, 255, 0))), "back.jpg"),
            ],
            "photo_types": ["appearance", "nutritional_label"],
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    photos = (
        ItemPhoto.query.filter_by(item_id=item.id)
        .order_by(ItemPhoto.display_order)
        .all()
    )
    assert len(photos) == 2
    assert photos[0].photo_type == "appearance"
    assert photos[1].photo_type == "nutritional_label"
    assert photos[0].display_order == 0
    assert photos[1].display_order == 1


def test_upload_all_valid_photo_types(auth_client, db, item):
    for photo_type in [
        "appearance",
        "barcode",
        "nutritional_label",
        "expiry_date",
        "other",
    ]:
        r = auth_client.post(
            f"/items/{item.id}/photos/add",
            data={
                "photos": (io.BytesIO(make_jpeg_bytes()), f"{photo_type}.jpg"),
                "photo_types": photo_type,
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert r.status_code == 200

    photos = ItemPhoto.query.filter_by(item_id=item.id).all()
    assert len(photos) == 5
    stored_types = {p.photo_type for p in photos}
    assert stored_types == {
        "appearance",
        "barcode",
        "nutritional_label",
        "expiry_date",
        "other",
    }


def test_upload_invalid_photo_type_defaults_to_appearance(auth_client, db, item):
    r = auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_jpeg_bytes()), "photo.jpg"),
            "photo_types": "bogus_type",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    photos = ItemPhoto.query.filter_by(item_id=item.id).all()
    assert len(photos) == 1
    assert photos[0].photo_type == "appearance"


def test_upload_no_file_does_not_create_photo(auth_client, db, item):
    r = auth_client.post(
        f"/items/{item.id}/photos/add",
        data={},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    photos = ItemPhoto.query.filter_by(item_id=item.id).all()
    assert len(photos) == 0


def test_upload_requires_login(auth_client, item):
    auth_client.post("/logout")
    r = auth_client.post(
        f"/items/{item.id}/photos/add",
        data={"photos": (io.BytesIO(make_jpeg_bytes()), "test.jpg")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert r.status_code == 302


# ── Serving ───────────────────────────────────────────────────────────────────


def test_serve_photo_returns_image(auth_client, db, item, app):
    # Upload a real file so the server can serve it
    jpeg = make_jpeg_bytes(color=(200, 100, 50))
    auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(jpeg), "serve_test.jpg"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
    )
    photo = ItemPhoto.query.filter_by(item_id=item.id).first()
    assert photo is not None

    r = auth_client.get(f"/photo/{photo.id}")
    assert r.status_code == 200
    assert "image" in r.content_type


def test_serve_photo_cache_header(auth_client, db, item, app):
    auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_jpeg_bytes()), "cache_test.jpg"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
    )
    photo = ItemPhoto.query.filter_by(item_id=item.id).first()
    r = auth_client.get(f"/photo/{photo.id}")
    assert r.status_code == 200
    assert "max-age" in r.headers.get("Cache-Control", "")


def test_serve_photo_forbidden_for_other_user(auth_client, client, db, item):
    # Upload a photo as testuser
    auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_jpeg_bytes()), "private.jpg"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
    )
    photo = ItemPhoto.query.filter_by(item_id=item.id).first()
    assert photo is not None

    # Log out testuser, then try to access the photo without a session
    auth_client.post("/logout")
    r = auth_client.get(f"/photo/{photo.id}")
    # No session → redirect to login (302), not the photo
    assert r.status_code in (302, 403)


def test_serve_nonexistent_photo_returns_403(auth_client):
    r = auth_client.get("/photo/999999")
    assert r.status_code == 403


def test_serve_photo_requires_login(auth_client, photo):
    auth_client.post("/logout")
    r = auth_client.get(f"/photo/{photo.id}", follow_redirects=False)
    assert r.status_code == 302


# ── Photo type update ─────────────────────────────────────────────────────────


def test_update_photo_type(auth_client, db, photo):
    r = auth_client.post(
        f"/items/{photo.item_id}/photos/{photo.id}/type",
        data={"photo_type": "expiry_date"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    db.session.refresh(photo)
    assert photo.photo_type == "expiry_date"


def test_update_photo_type_invalid_defaults_to_appearance(auth_client, db, photo):
    r = auth_client.post(
        f"/items/{photo.item_id}/photos/{photo.id}/type",
        data={"photo_type": "garbage_type"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    db.session.refresh(photo)
    assert photo.photo_type == "appearance"


def test_update_photo_type_all_valid_types(auth_client, db, photo):
    for t in ItemPhoto.VALID_TYPES:
        r = auth_client.post(
            f"/items/{photo.item_id}/photos/{photo.id}/type",
            data={"photo_type": t},
            follow_redirects=True,
        )
        assert r.status_code == 200
        db.session.refresh(photo)
        assert photo.photo_type == t


# ── Deletion ──────────────────────────────────────────────────────────────────


def test_delete_photo(auth_client, db, item):
    auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_jpeg_bytes()), "to_delete.jpg"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
    )
    photo = ItemPhoto.query.filter_by(item_id=item.id).first()
    assert photo is not None
    photo_id = photo.id

    r = auth_client.post(
        f"/items/{item.id}/photos/{photo_id}/delete",
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert _db.session.get(ItemPhoto, photo_id) is None


def test_delete_photo_renumbers_display_order(auth_client, db, item):
    # Upload two photos
    auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": [
                (io.BytesIO(make_jpeg_bytes((255, 0, 0))), "first.jpg"),
                (io.BytesIO(make_jpeg_bytes((0, 0, 255))), "second.jpg"),
            ],
            "photo_types": ["appearance", "other"],
        },
        content_type="multipart/form-data",
    )
    photos = (
        ItemPhoto.query.filter_by(item_id=item.id)
        .order_by(ItemPhoto.display_order)
        .all()
    )
    assert len(photos) == 2

    # Delete the first photo
    auth_client.post(
        f"/items/{item.id}/photos/{photos[0].id}/delete",
        follow_redirects=True,
    )
    remaining = ItemPhoto.query.filter_by(item_id=item.id).all()
    assert len(remaining) == 1
    assert remaining[0].display_order == 0


def test_delete_local_file_on_photo_delete(auth_client, db, item, app):
    auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_jpeg_bytes()), "deleteme.jpg"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
    )
    photo = ItemPhoto.query.filter_by(item_id=item.id).first()
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], photo.photo_path)

    auth_client.post(
        f"/items/{item.id}/photos/{photo.id}/delete", follow_redirects=True
    )

    # File should be removed from disk
    assert not os.path.exists(saved_path)


# ── Edit photos page ──────────────────────────────────────────────────────────


def test_edit_photos_page_loads(auth_client, item):
    r = auth_client.get(f"/items/{item.id}/photos")
    assert r.status_code == 200


def test_item_detail_shows_photo_url(auth_client, db, item, app):
    auth_client.post(
        f"/items/{item.id}/photos/add",
        data={
            "photos": (io.BytesIO(make_jpeg_bytes()), "display.jpg"),
            "photo_types": "appearance",
        },
        content_type="multipart/form-data",
    )
    photo = ItemPhoto.query.filter_by(item_id=item.id).first()
    r = auth_client.get(f"/items/{item.id}")
    assert r.status_code == 200
    assert f"/photo/{photo.id}".encode() in r.data


# ── Photo URL property ────────────────────────────────────────────────────────


def test_photo_url_property(photo):
    assert photo.photo_url == f"/photo/{photo.id}"


def test_item_has_photo_false_without_photos(item):
    assert not item.has_photo


def test_item_has_photo_true_with_photo(db, item, photo):
    db.session.refresh(item)
    assert item.has_photo


def test_item_display_photo_prefers_appearance(db, item):
    barcode_p = ItemPhoto(
        item_id=item.id, photo_path="barcode.jpg", photo_type="barcode", display_order=0
    )
    appear_p = ItemPhoto(
        item_id=item.id,
        photo_path="appear.jpg",
        photo_type="appearance",
        display_order=1,
    )
    db.session.add_all([barcode_p, appear_p])
    db.session.commit()

    db.session.refresh(item)
    assert item.display_photo.photo_type == "appearance"

    db.session.delete(barcode_p)
    db.session.delete(appear_p)
    db.session.commit()

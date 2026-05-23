"""Smoke tests that catch import errors before they reach production."""


def test_app_factory_runs(app):
    assert app is not None


def test_pantry_items_importable_from_canonical_location():
    from app.pantry_data import PANTRY_ITEMS

    assert isinstance(PANTRY_ITEMS, list)
    assert len(PANTRY_ITEMS) > 0


def test_pantry_items_not_in_forms():
    import importlib

    forms = importlib.import_module("app.perishables.forms")
    assert not hasattr(
        forms, "PANTRY_ITEMS"
    ), "PANTRY_ITEMS should live in app.pantry_data, not app.perishables.forms"

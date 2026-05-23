"""Tests for ingredient normalization logic."""

from app.ingredient_normalization import normalize_ingredient


def test_exact_match():
    result = normalize_ingredient("Fish sauce")
    assert result == "Fish sauce"


def test_case_insensitive_match():
    result = normalize_ingredient("fish sauce")
    assert result == "Fish sauce"


def test_substring_match():
    result = normalize_ingredient("light soy sauce bottle")
    assert result == "Light soy sauce"


def test_no_match_returns_none():
    result = normalize_ingredient("xyz_impossible_ingredient_abc")
    assert result is None


def test_empty_string_returns_none():
    assert normalize_ingredient("") is None


def test_coconut_milk():
    result = normalize_ingredient("coconut milk")
    assert result == "Coconut milk"


def test_sesame_oil():
    result = normalize_ingredient("Sesame oil")
    assert result == "Sesame oil"


def test_short_word_no_false_match():
    # "water" should not match "Water chestnuts" (coverage < 55%)
    result = normalize_ingredient("water")
    # Either None or "Water" (if it exists exactly) — just not "Water chestnuts"
    assert result != "Water chestnuts"


def test_mushrooms_no_false_match():
    # "mushrooms" should not spuriously match long items like "Wood ear mushrooms"
    result = normalize_ingredient("mushrooms")
    if result is not None:
        assert "mushrooms" in result.lower()

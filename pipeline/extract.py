"""
JSON-LD extraction from recipe pages.

Most food blogs publish schema.org/Recipe structured data as a
<script type="application/ld+json"> block. This is far more reliable
than HTML scraping because it's machine-written and stable across
layout redesigns.
"""

import re
import json
import html.parser
from typing import Optional

from pipeline.transform import (
    clean_ingredient,
    parse_duration_minutes,
    format_cook_time,
    infer_difficulty,
    slugify,
)


class _JSONLDExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts: list[str] = []
        self._in_jsonld = False
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            if dict(attrs).get("type") == "application/ld+json":
                self._in_jsonld = True
                self._buf = []

    def handle_endtag(self, tag):
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            self.scripts.append("".join(self._buf))

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf.append(data)


def find_recipe_jsonld(html_text: str) -> Optional[dict]:
    """Return the first schema.org/Recipe object found in any JSON-LD block."""
    extractor = _JSONLDExtractor()
    try:
        extractor.feed(html_text)
    except html.parser.HTMLParseError:
        pass

    for script in extractor.scripts:
        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict) and "@graph" in data:
            items = data["@graph"]
        elif isinstance(data, list):
            items = data
        else:
            items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue
            type_ = item.get("@type", "")
            if isinstance(type_, list):
                is_recipe = any("Recipe" in t for t in type_)
            else:
                is_recipe = "Recipe" in str(type_)
            if is_recipe:
                return item

    return None


def find_recipe_nextdata(html_text: str) -> Optional[dict]:
    """Extract recipe data from a Next.js __NEXT_DATA__ JSON script block.

    Returns the first query's data dict, which on Made with Lau recipe pages
    contains the full recipe object from Sanity CMS.
    """
    marker = '<script id="__NEXT_DATA__" type="application/json">'
    start = html_text.find(marker)
    if start == -1:
        return None
    start += len(marker)
    end = html_text.find("</script>", start)
    if end == -1:
        return None
    try:
        obj = json.loads(html_text[start:end])
        queries = obj["props"]["pageProps"]["trpcState"]["queries"]
        if not queries:
            return None
        return queries[0]["state"]["data"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None


def map_nextdata_to_recipe(
    data: dict,
    source_name: str,
    cuisine: str,
    url: str,
) -> Optional[dict]:
    """Map a Made with Lau __NEXT_DATA__ recipe dict to our internal recipe shape.

    Ingredients come from ingredientsArray (Sanity CMS format). Times are
    already in integer minutes (prepTime, totalTime).
    """
    name = data.get("englishTitle", "").strip()
    if not name:
        return None

    raw_ingredients = [
        item
        for item in data.get("ingredientsArray", [])
        if item.get("_type") == "ingredient"
    ]
    if not raw_ingredients:
        return None

    ingredients = [
        item["item"].strip().lower() for item in raw_ingredients if item.get("item")
    ]
    ingredients = [i for i in ingredients if i]
    if not ingredients:
        return None

    total_mins = data.get("totalTime")

    return {
        "id": slugify(name),
        "name": name,
        "source": source_name,
        "source_url": url,
        "cuisine": cuisine,
        "cook_time": format_cook_time(total_mins),
        "difficulty": infer_difficulty(total_mins),
        "ingredients": ingredients,
    }


_DATE_RE = re.compile(r"^\w+ \d+, \d{4}$|^\d{4}-\d{2}-\d{2}$")
_META_RE = re.compile(
    r"posted by|jump to recipe|print recipe|rate this recipe", re.IGNORECASE
)
_INSTRUCTIONS_RE = re.compile(
    r"\b(instructions?|methods?|directions?|steps?|how to|procedure)\b", re.IGNORECASE
)
_NAV_TERMS_RE = re.compile(
    r"\b(contact|about|shop|careers?|privacy|terms)\b", re.IGNORECASE
)


class _HTMLRecipeExtractor(html.parser.HTMLParser):
    """Extract recipe data from plain HTML without relying on JSON-LD or recipe plugins.

    Strategy (tried in order):
    1. WP Recipe Maker class names (wprm-recipe-ingredient-name)
    2. Tasty Recipes class names (tasty-recipes-ingredients)
    3. Heading-based fallback: open an "ingredient section" at any short heading
       whose text contains "ingredient", and close it only when an "Instructions"
       heading is found. All <ul> blocks within the section are collected and
       combined — this handles recipes whose ingredients are split into sub-sections
       (e.g. Dough / Filling / Sauce).
    """

    def __init__(self):
        super().__init__()
        self._all_text: list[str] = []

        # Plugin-based collection
        self._in_wprm_ingredient = False
        self._wprm_ingredients: list[str] = []
        self._wprm_buf: list[str] = []
        self._in_tasty_ingredient_section = False
        self._in_tasty_li = False
        self._tasty_li_buf: list[str] = []
        self._tasty_ingredients: list[str] = []

        # Heading-based: track the ingredient section and all UL blocks within it
        self._in_heading = False
        self._heading_buf: list[str] = []
        self._in_ingredient_section = (
            False  # True between "Ingredients" and "Instructions" headings
        )
        self._current_candidate: Optional[list[str]] = None  # None = not in a UL
        self._all_candidates: list[list[str]] = []
        self._in_ingredient_li = False
        self._ingredient_li_buf: list[str] = []

    @staticmethod
    def _is_ingredient_heading(text: str) -> bool:
        """True only for headings that specifically name the ingredients section.

        Requires "ingredient(s)" to be the first or last word — this rejects
        recipe titles like "5 Ingredient Mushroom Pasta" where "ingredient"
        appears in the middle, while accepting "Ingredients", "Recipe Ingredients",
        "Ingredients for the Dough", etc.
        """
        words = text.strip().split()
        if not words:
            return False
        return words[0].startswith("ingredient") or words[-1].startswith("ingredient")

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "")

        # WP Recipe Maker
        if "wprm-recipe-ingredient-name" in classes:
            self._in_wprm_ingredient = True
            self._wprm_buf = []
            return

        # Tasty Recipes
        if "tasty-recipes-ingredients" in classes:
            self._in_tasty_ingredient_section = True
        if self._in_tasty_ingredient_section and tag == "li":
            self._in_tasty_li = True
            self._tasty_li_buf = []

        # Heading detection
        if tag in ("h1", "h2", "h3", "h4"):
            self._in_heading = True
            self._heading_buf = []
            return

        # Every <ul> while in the ingredient section starts a new candidate block
        if (
            self._in_ingredient_section
            and tag == "ul"
            and self._current_candidate is None
        ):
            self._current_candidate = []
            return

        if self._current_candidate is not None and tag == "li":
            self._in_ingredient_li = True
            self._ingredient_li_buf = []

    def handle_endtag(self, tag):
        # WP Recipe Maker
        if self._in_wprm_ingredient and tag in ("span", "div", "p"):
            text = "".join(self._wprm_buf).strip()
            if text:
                self._wprm_ingredients.append(text)
            self._in_wprm_ingredient = False

        # Tasty Recipes
        if self._in_tasty_li and tag == "li":
            text = "".join(self._tasty_li_buf).strip()
            if text:
                self._tasty_ingredients.append(text)
            self._in_tasty_li = False
            self._tasty_li_buf = []

        # Heading end — open or close the ingredient section
        if tag in ("h1", "h2", "h3", "h4") and self._in_heading:
            self._in_heading = False
            heading_text = "".join(self._heading_buf).strip().lower()
            if self._is_ingredient_heading(heading_text):
                self._in_ingredient_section = True
            elif self._in_ingredient_section and _INSTRUCTIONS_RE.search(heading_text):
                # Only close on "Instructions / Method / Steps" — not on sub-section headings
                self._in_ingredient_section = False

        # Ingredient <li> end
        if self._in_ingredient_li and tag == "li":
            text = "".join(self._ingredient_li_buf).strip()
            if text and self._current_candidate is not None:
                self._current_candidate.append(text)
            self._in_ingredient_li = False
            self._ingredient_li_buf = []

        # Ingredient <ul> end — save this candidate block and reset for next UL
        if tag == "ul" and self._current_candidate is not None:
            if self._current_candidate:
                self._all_candidates.append(self._current_candidate)
            self._current_candidate = None

    def handle_data(self, data):
        self._all_text.append(data)
        if self._in_wprm_ingredient:
            self._wprm_buf.append(data)
        if self._in_tasty_li:
            self._tasty_li_buf.append(data)
        if self._in_heading:
            self._heading_buf.append(data)
        if self._in_ingredient_li:
            self._ingredient_li_buf.append(data)

    def _filter_candidate(self, items: list[str]) -> list[str]:
        return [
            item
            for item in items
            if len(item) <= 90  # prose descriptions are long
            and not item.rstrip().endswith(".")  # full-sentence notes end with a period
            and "!" not in item  # exclamatory prose
            and not _DATE_RE.search(item)
            and not _META_RE.search(item)
            and not _NAV_TERMS_RE.fullmatch(item.strip())
        ]

    def _score_candidate(self, items: list[str]) -> float:
        """Score 0–1: fraction of items that look like real ingredients."""
        if not items:
            return 0.0
        return len(self._filter_candidate(items)) / len(items)

    def best_ingredients(self) -> list[str]:
        """Return combined ingredients from all valid section candidates, deduplicated."""
        if self._wprm_ingredients:
            return self._wprm_ingredients
        if self._tasty_ingredients:
            return self._tasty_ingredients
        if not self._all_candidates:
            return []

        # Combine all well-scoring candidates (handles Dough/Filling/Sauce sub-sections).
        # Drop candidates that score poorly (stray related-recipe or nav UL blocks).
        combined: list[str] = []
        seen: set[str] = set()
        for candidate in self._all_candidates:
            if self._score_candidate(candidate) >= 0.6:
                for item in self._filter_candidate(candidate):
                    key = item.lower().strip()
                    if key not in seen:
                        seen.add(key)
                        combined.append(item)

        return combined

    def extract_cook_mins(self) -> Optional[int]:
        full_text = " ".join(self._all_text)
        pattern = re.compile(
            r"(total|cook)\s+time\s*[:\-]?\s*(\d+)\s*(?:min|minute)",
            re.IGNORECASE,
        )
        best: Optional[int] = None
        for m in pattern.finditer(full_text):
            label, mins = m.group(1).lower(), int(m.group(2))
            if label == "total":
                return mins
            if best is None:
                best = mins
        return best


def find_recipe_html(html_text: str, name_hint: str) -> Optional[dict]:
    """Extract recipe data from plain HTML (no JSON-LD required).

    Returns a dict with {name, ingredients, cook_mins} or None if fewer than
    3 ingredients are found (indicates a non-recipe page).
    """
    extractor = _HTMLRecipeExtractor()
    try:
        extractor.feed(html_text)
    except html.parser.HTMLParseError:
        pass

    ingredients = extractor.best_ingredients()
    if len(ingredients) < 3:
        return None

    return {
        "name": name_hint,
        "ingredients": ingredients,
        "cook_mins": extractor.extract_cook_mins(),
    }


def map_html_to_recipe(
    data: dict,
    source_name: str,
    cuisine: str,
    url: str,
) -> Optional[dict]:
    """Map a find_recipe_html() result to our internal recipe shape."""
    name = data.get("name", "").strip()
    if not name:
        return None

    raw_ingredients = data.get("ingredients", [])
    ingredients = [clean_ingredient(i) for i in raw_ingredients if i.strip()]
    ingredients = [i for i in ingredients if i]
    if not ingredients:
        return None

    cook_mins = data.get("cook_mins")

    return {
        "id": slugify(name),
        "name": name,
        "source": source_name,
        "source_url": url,
        "cuisine": cuisine,
        "cook_time": format_cook_time(cook_mins),
        "difficulty": infer_difficulty(cook_mins),
        "ingredients": ingredients,
    }


def map_to_recipe(
    data: dict,
    source_name: str,
    cuisine: str,
    url: str,
) -> Optional[dict]:
    """Map a schema.org Recipe dict to our internal recipe shape.

    Returns None if required fields (name, ingredients) are missing.
    """
    name = data.get("name", "").strip()
    if not name:
        return None

    raw_ingredients = data.get("recipeIngredient", [])
    if not raw_ingredients:
        return None

    ingredients = [clean_ingredient(i) for i in raw_ingredients if i.strip()]
    ingredients = [i for i in ingredients if i]
    if not ingredients:
        return None

    cook_time_raw = (
        data.get("cookTime") or data.get("totalTime") or data.get("prepTime")
    )
    cook_mins = parse_duration_minutes(cook_time_raw)
    total_mins = parse_duration_minutes(data.get("totalTime")) or cook_mins

    return {
        "id": slugify(name),
        "name": name,
        "source": source_name,
        "source_url": url,
        "cuisine": cuisine,
        "cook_time": format_cook_time(cook_mins),
        "difficulty": infer_difficulty(total_mins),
        "ingredients": ingredients,
    }

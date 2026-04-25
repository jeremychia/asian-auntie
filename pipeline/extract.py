"""
JSON-LD extraction from recipe pages.

Most food blogs publish schema.org/Recipe structured data as a
<script type="application/ld+json"> block. This is far more reliable
than HTML scraping because it's machine-written and stable across
layout redesigns.
"""

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

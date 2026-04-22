#!/usr/bin/env python3
"""
Discover and scrape recipe metadata from trusted Asian food blogs.

Strategy:
  1. Crawl category/index pages to find recipe URLs (handles pagination)
  2. For each recipe page, extract JSON-LD schema.org/Recipe data
  3. Emit a new data.py (or print to stdout)

Usage:
  uv run python scripts/scrape_recipes.py
  uv run python scripts/scrape_recipes.py --output app/recipes/data.py
  uv run python scripts/scrape_recipes.py --limit 10 --delay 2.0
  uv run python scripts/scrape_recipes.py --source "Rasa Malaysia"
"""

import sys
import json
import time
import re
import argparse
import urllib.request
import urllib.parse
import urllib.error
import html.parser
import socket
from collections import defaultdict
from typing import Optional

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Each entry: (category_url, cuisine, source_name, max_pages)
# Category URLs must be real pages that list recipes with pagination.
CATEGORY_SOURCES = [
    # Rasa Malaysia — confirmed JSON-LD + WordPress /page/N/ pagination
    (
        "https://rasamalaysia.com/category/malaysian-recipes/",
        "Malaysian",
        "Rasa Malaysia",
        5,
    ),
    ("https://rasamalaysia.com/category/thai-recipes/", "Thai", "Rasa Malaysia", 3),
    (
        "https://rasamalaysia.com/category/chinese-recipes/",
        "Chinese",
        "Rasa Malaysia",
        3,
    ),
    (
        "https://rasamalaysia.com/category/indonesian-recipes/",
        "Indonesian",
        "Rasa Malaysia",
        2,
    ),
    # The Woks of Life
    (
        "https://thewoksoflife.com/recipes/chinese-recipes/",
        "Chinese",
        "The Woks of Life",
        3,
    ),
    ("https://thewoksoflife.com/recipes/asian-recipes/", "Thai", "The Woks of Life", 2),
    # Panlasang Pinoy
    (
        "https://panlasangpinoy.com/categories/lutong-pinoy/",
        "Filipino",
        "Panlasang Pinoy",
        5,
    ),
    # Made with Lau
    ("https://www.madewithlau.com/recipes", "Chinese", "Made with Lau", 3),
    # Hot Thai Kitchen
    ("https://hot-thai-kitchen.com/recipe-index/", "Thai", "Hot Thai Kitchen", 2),
    # Hungry Huy (Vietnamese)
    ("https://www.hungryhuy.com/recipe-index/", "Vietnamese", "Hungry Huy", 2),
    # Nyonya Cooking
    ("https://www.nyonyacooking.com/recipes", "Malaysian", "Nyonya Cooking", 3),
]

# URL fragments that indicate a non-recipe page
_SKIP_RE = re.compile(
    r"/(category|categories|tag|tags|page|author|search|wp-content|wp-admin"
    r"|feed|sitemap|about|contact|privacy|terms|shop|cart|checkout"
    r"|account|login|register|newsletter|subscribe|index|recipe-index"
    r"|collections|courses|ingredients)/",
    re.IGNORECASE,
)

_MEDIA_RE = re.compile(r"\.(jpg|jpeg|png|gif|pdf|mp4|webp|svg)($|\?)", re.IGNORECASE)


# ── HTML parsers ──────────────────────────────────────────────────────────────


class LinkExtractor(html.parser.HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href and not href.startswith(("#", "mailto:", "tel:")):
                full = urllib.parse.urljoin(self.base_url, href)
                self.links.append(full)


class JSONLDExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts: list[str] = []
        self._in_jsonld = False
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs_dict = dict(attrs)
            if attrs_dict.get("type") == "application/ld+json":
                self._in_jsonld = True
                self._buf = []

    def handle_endtag(self, tag):
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            self.scripts.append("".join(self._buf))

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf.append(data)


# ── HTTP helpers ──────────────────────────────────────────────────────────────

_last_fetch: dict[str, float] = defaultdict(float)


def fetch(url: str, delay: float = 1.5, timeout: int = 20) -> Optional[str]:
    domain = urllib.parse.urlparse(url).netloc
    elapsed = time.time() - _last_fetch[domain]
    if elapsed < delay:
        time.sleep(delay - elapsed)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html_bytes = resp.read()
            _last_fetch[domain] = time.time()
            return html_bytes.decode("utf-8", errors="ignore")
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        socket.timeout,
        OSError,
    ) as e:
        print(f"  [FETCH ERROR] {url} — {e}", file=sys.stderr)
        _last_fetch[domain] = time.time()
        return None


# ── Recipe extraction ─────────────────────────────────────────────────────────


def parse_duration_minutes(iso: Optional[str]) -> Optional[int]:
    """Parse ISO 8601 duration (PT45M, PT1H30M) to total minutes."""
    if not iso:
        return None
    m = re.search(r"(?:(\d+)H)?(?:(\d+)M)?", iso)
    if not m or not (m.group(1) or m.group(2)):
        return None
    hours = int(m.group(1) or 0)
    mins = int(m.group(2) or 0)
    total = hours * 60 + mins
    return total if total > 0 else None


def format_cook_time(minutes: Optional[int]) -> str:
    if not minutes:
        return "unknown"
    if minutes < 60:
        return f"{minutes} min"
    h, m = divmod(minutes, 60)
    return f"{h}h {m}min" if m else f"{h}h"


def infer_difficulty(total_minutes: Optional[int]) -> str:
    if not total_minutes:
        return "Medium"
    if total_minutes <= 20:
        return "Easy"
    if total_minutes <= 45:
        return "Medium"
    return "Hard"


def clean_ingredient(text: str) -> str:
    """Strip quantities, units, and parenthetical notes; normalize ingredient text."""
    text = text.strip()
    # Strip parenthetical prep notes like "(seeded)", "(or to taste)", "(about 2 cups)"
    text = re.sub(r"\s*\(.*?\)", "", text)
    # Remove quantity + unit prefix like "2 cups", "1/2 tsp", "½ pound", "20-30"
    text = re.sub(
        r"^[\d½¼¾⅓⅔\s/–-]+\s*"
        r"(?:cup|tbsp|tsp|tablespoon|teaspoon|pound|lb|oz|g|gram|kg|ml|l|liter|litre"
        r"|piece|clove|stalk|bunch|handful|pinch|dash|sprig|head|slice|sheet"
        r"|can|tin|package|pkg|bag|bottle|jar|drop|quart|pint)s?"
        r"(?:\s+of)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Remove standalone leading numbers / ranges like "2 " or "20-30 " at start
    text = re.sub(r"^[\d][\d\s–-]*\s+", "", text)
    # Collapse extra whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def extract_recipe_from_jsonld(html_text: str) -> Optional[dict]:
    """Return the first schema.org/Recipe object found in JSON-LD scripts."""
    extractor = JSONLDExtractor()
    try:
        extractor.feed(html_text)
    except html.parser.HTMLParseError:
        pass

    for script in extractor.scripts:
        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            continue

        # Unwrap @graph
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
                match = any("Recipe" in t for t in type_)
            else:
                match = "Recipe" in str(type_)
            if match:
                return item

    return None


def jsonld_to_recipe(
    data: dict,
    source_name: str,
    cuisine: str,
    url: str,
) -> Optional[dict]:
    name = data.get("name", "").strip()
    if not name:
        return None

    raw_ingredients = data.get("recipeIngredient", [])
    if not raw_ingredients:
        return None

    ingredients = [clean_ingredient(i) for i in raw_ingredients if i.strip()]
    ingredients = [i for i in ingredients if i]  # drop empties after cleaning

    cook_time_raw = (
        data.get("cookTime") or data.get("totalTime") or data.get("prepTime")
    )
    cook_mins = parse_duration_minutes(cook_time_raw)

    total_time_raw = data.get("totalTime")
    total_mins = parse_duration_minutes(total_time_raw) or cook_mins

    # Always use our cuisine mapping — JSON-LD values are often verbose
    # (e.g. "Malaysian Recipes") and inconsistent across sites.
    final_cuisine = cuisine

    return {
        "id": slugify(name),
        "name": name,
        "source": source_name,
        "source_url": url,
        "cuisine": final_cuisine,
        "cook_time": format_cook_time(cook_mins),
        "difficulty": infer_difficulty(total_mins),
        "ingredients": ingredients,
    }


# ── Category crawling ─────────────────────────────────────────────────────────


def is_recipe_link(url: str, base_domain: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc and parsed.netloc != base_domain:
        return False
    if _SKIP_RE.search(parsed.path):
        return False
    if _MEDIA_RE.search(parsed.path):
        return False
    path = parsed.path.strip("/")
    if not path or path.count("/") > 1:
        return False
    return True


def paginate_url(base_category_url: str, page: int) -> str:
    """Generate page N URL using WordPress /page/N/ convention."""
    if page == 1:
        return base_category_url
    base = base_category_url.rstrip("/")
    return f"{base}/page/{page}/"


def discover_recipe_urls(
    category_url: str,
    max_pages: int,
    delay: float,
) -> list[str]:
    base_domain = urllib.parse.urlparse(category_url).netloc
    found: set[str] = set()

    for page_num in range(1, max_pages + 1):
        page_url = paginate_url(category_url, page_num)
        print(f"  Crawling: {page_url}", file=sys.stderr)
        html_text = fetch(page_url, delay=delay)
        if not html_text:
            break

        extractor = LinkExtractor(page_url)
        try:
            extractor.feed(html_text)
        except html.parser.HTMLParseError:
            pass

        page_recipes = [
            urllib.parse.urljoin(page_url, link)
            for link in extractor.links
            if is_recipe_link(urllib.parse.urljoin(page_url, link), base_domain)
        ]
        # Normalise: strip query/fragment, strip trailing slash for dedup
        page_recipes = [
            urllib.parse.urlunparse(
                urllib.parse.urlparse(u)._replace(query="", fragment="")
            ).rstrip("/")
            for u in page_recipes
        ]

        new = set(page_recipes) - found
        if not new:
            break  # No new links — probably past last page
        found.update(new)

    return sorted(found)


# ── Main scraping flow ────────────────────────────────────────────────────────


def scrape_all(
    sources: list[tuple],
    limit: Optional[int],
    delay: float,
    filter_source: Optional[str],
) -> list[dict]:
    seen_urls: set[str] = set()
    seen_ids: set[str] = set()
    recipes: list[dict] = []

    for category_url, cuisine, source_name, max_pages in sources:
        if filter_source and filter_source.lower() not in source_name.lower():
            continue

        print(f"\n[{source_name}] cuisine={cuisine} — {category_url}", file=sys.stderr)
        recipe_urls = discover_recipe_urls(category_url, max_pages, delay)
        print(f"  Found {len(recipe_urls)} candidate URLs", file=sys.stderr)

        for url in recipe_urls:
            if url in seen_urls:
                continue
            seen_urls.add(url)

            if limit and len(recipes) >= limit:
                print(f"  Reached limit of {limit} recipes", file=sys.stderr)
                return recipes

            html_text = fetch(url, delay=delay)
            if not html_text:
                continue

            jsonld = extract_recipe_from_jsonld(html_text)
            if not jsonld:
                print(f"  [NO JSON-LD] {url}", file=sys.stderr)
                continue

            recipe = jsonld_to_recipe(jsonld, source_name, cuisine, url)
            if not recipe:
                print(f"  [SKIP] {url} — missing name or ingredients", file=sys.stderr)
                continue

            # Deduplicate by id
            if recipe["id"] in seen_ids:
                print(f"  [DUP] {recipe['id']}", file=sys.stderr)
                continue
            seen_ids.add(recipe["id"])

            print(f"  [OK] {recipe['name']}", file=sys.stderr)
            recipes.append(recipe)

    return recipes


# ── Output formatting ─────────────────────────────────────────────────────────


def _repr_list(items: list[str], indent: int) -> str:
    pad = " " * indent
    inner = (",\n" + pad + "    ").join(f'"{i}"' for i in items)
    return f"[\n{pad}    {inner},\n{pad}]"


def emit_data_py(recipes: list[dict]) -> str:
    lines = [
        "# Curated Malaysian and Southeast Asian recipe corpus.",
        "# Instructions are never stored here — we only hold enough metadata to compute",
        "# ingredient match % and link to the source.",
        "# Generated by scripts/scrape_recipes.py — do not edit by hand.",
        "",
        "RECIPES = [",
    ]

    by_cuisine: dict[str, list[dict]] = defaultdict(list)
    for r in recipes:
        by_cuisine[r["cuisine"]].append(r)

    cuisine_order = [
        "Malaysian",
        "Thai",
        "Filipino",
        "Indonesian",
        "Vietnamese",
        "Singaporean",
        "Chinese",
    ]
    ordered_cuisines = cuisine_order + [
        c for c in sorted(by_cuisine) if c not in cuisine_order
    ]

    for cuisine in ordered_cuisines:
        if cuisine not in by_cuisine:
            continue
        lines.append(f"    # ── {cuisine} {'─' * (73 - len(cuisine))}")
        for r in by_cuisine[cuisine]:
            lines.append("    {")
            lines.append(f'        "id": "{r["id"]}",')
            lines.append(f'        "name": "{r["name"]}",')
            lines.append(f'        "source": "{r["source"]}",')
            lines.append(f'        "source_url": "{r["source_url"]}",')
            lines.append(f'        "cuisine": "{r["cuisine"]}",')
            lines.append(f'        "cook_time": "{r["cook_time"]}",')
            lines.append(f'        "difficulty": "{r["difficulty"]}",')
            ing_repr = _repr_list(r["ingredients"], indent=8)
            lines.append(f'        "ingredients": {ing_repr},')
            lines.append("    },")

    lines.append("]")
    lines.append("")
    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Asian recipe metadata from food blogs"
    )
    parser.add_argument(
        "--output", type=str, help="Write data.py to this path (default: stdout)"
    )
    parser.add_argument("--limit", type=int, help="Stop after N recipes total")
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Per-domain delay in seconds (default 2.0)",
    )
    parser.add_argument(
        "--source",
        type=str,
        help='Only scrape sites matching this name (e.g. "Rasa Malaysia")',
    )
    args = parser.parse_args()

    recipes = scrape_all(
        sources=CATEGORY_SOURCES,
        limit=args.limit,
        delay=args.delay,
        filter_source=args.source,
    )

    print(f"\nScraped {len(recipes)} recipes total.", file=sys.stderr)

    output = emit_data_py(recipes)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()

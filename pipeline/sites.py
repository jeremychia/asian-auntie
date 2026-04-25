"""
Declarative configuration for each recipe source site.

To add a new site, add an entry to SITES with the appropriate keys.
See README.md for a full walkthrough.

Schema
------
Each site dict must contain:
  name         str   — Display name, stored as recipe["source"]
  discovery    str   — "category" or "sitemap"
  delay        float — Minimum seconds between requests to this domain

For discovery="category":
  categories   list[tuple[str, str]]  — (category_url, cuisine) pairs
  max_pages    int                    — Max paginated pages to crawl per category

For discovery="sitemap":
  sitemap_index_url  str            — URL of the sitemap index XML
  cuisine_default    str            — Cuisine label to assign all recipes
  url_pattern        str | None     — Regex to filter sitemap URLs (optional)
"""

SITES: dict[str, dict] = {
    # ── Rasa Malaysia ─────────────────────────────────────────────────────────
    "rasa_malaysia": {
        "name": "Rasa Malaysia",
        "discovery": "category",
        "delay": 2.0,
        "max_pages": 10,
        "categories": [
            ("https://rasamalaysia.com/recipes/malaysian-recipes/", "Malaysian"),
            ("https://rasamalaysia.com/recipes/thai-recipes/", "Thai"),
            ("https://rasamalaysia.com/recipes/chinese-recipes/", "Chinese"),
            ("https://rasamalaysia.com/recipes/indonesian-recipes/", "Indonesian"),
        ],
    },
    # ── The Woks of Life ──────────────────────────────────────────────────────
    "woks_of_life": {
        "name": "The Woks of Life",
        "discovery": "category",
        "delay": 2.0,
        "max_pages": 5,
        "categories": [
            ("https://thewoksoflife.com/recipes/chinese-recipes/", "Chinese"),
            ("https://thewoksoflife.com/recipes/asian-recipes/", "Thai"),
        ],
    },
    # ── Panlasang Pinoy ───────────────────────────────────────────────────────
    "panlasang_pinoy": {
        "name": "Panlasang Pinoy",
        "discovery": "category",
        "delay": 2.0,
        "max_pages": 5,
        "categories": [
            ("https://panlasangpinoy.com/categories/lutong-pinoy/", "Filipino"),
        ],
    },
    # ── Hungry Huy ────────────────────────────────────────────────────────────
    "hungry_huy": {
        "name": "Hungry Huy",
        "discovery": "category",
        "delay": 2.0,
        "max_pages": 3,
        "categories": [
            ("https://www.hungryhuy.com/recipe-index/", "Vietnamese"),
        ],
    },
    # ── Hot Thai Kitchen ──────────────────────────────────────────────────────
    "hot_thai_kitchen": {
        "name": "Hot Thai Kitchen",
        "discovery": "category",
        "delay": 2.0,
        "max_pages": 3,
        "categories": [
            ("https://hot-thai-kitchen.com/recipe-index/", "Thai"),
        ],
    },
    # ── Made with Lau ─────────────────────────────────────────────────────────
    "made_with_lau": {
        "name": "Made with Lau",
        "discovery": "category",
        "delay": 2.0,
        "max_pages": 3,
        "categories": [
            ("https://www.madewithlau.com/recipes", "Chinese"),
        ],
    },
    # ── Nyonya Cooking ────────────────────────────────────────────────────────
    "nyonya_cooking": {
        "name": "Nyonya Cooking",
        "discovery": "category",
        "delay": 2.0,
        "max_pages": 3,
        "categories": [
            ("https://www.nyonyacooking.com/recipes", "Malaysian"),
        ],
    },
}

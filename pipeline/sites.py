"""
Declarative configuration for each recipe source site.

To add a new site, add an entry to SITES with the appropriate keys.
See README.md for a full walkthrough.

Schema
------
Each site dict must contain:
  name         str   — Display name, stored as recipe["source"]
  discovery    str   — "category", "sitemap", or "youtube"
  delay        float — Minimum seconds between requests to this domain

For discovery="category":
  categories   list[tuple[str, str]]  — (category_url, cuisine) pairs
  max_pages    int                    — Max paginated pages to crawl per category

For discovery="sitemap":
  sitemap_index_url  str            — URL of the sitemap index XML
  cuisine_default    str            — Cuisine label to assign all recipes
  url_pattern        str | None     — Regex to filter sitemap URLs (optional)

For discovery="youtube":
  channel_url  str            — YouTube channel URL (the /videos page)
  cuisine      str            — Cuisine label applied to all videos
  max_videos   int | None     — Cap on videos to discover (optional)
  Requires ANTHROPIC_API_KEY env var. Uses yt-dlp + Claude to extract recipes
  from video descriptions and auto-generated captions (any language → English).
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
    # Next.js site — recipe data lives in __NEXT_DATA__ JSON, not JSON-LD.
    # Discovery via flat sitemap (urlset, not a sitemap index).
    "made_with_lau": {
        "name": "Made with Lau",
        "discovery": "sitemap",
        "sitemap_index_url": "https://www.madewithlau.com/sitemap.xml",
        "url_pattern": r"https://www\.madewithlau\.com/recipes/[^/]+$",
        "cuisine_default": "Chinese",
        "delay": 2.0,
        "extraction": "nextdata",
    },
    # ── Shivangi Kooks ────────────────────────────────────────────────────────
    # No JSON-LD — uses heading-based HTML extraction (see extract.py).
    # Cuisine set to Indian for all categories; Korean-inspired recipes
    # included under the same label as an acceptable approximation.
    "shivangi_kooks": {
        "name": "Shivangi Kooks",
        "discovery": "category",
        "delay": 2.0,
        "max_pages": 3,
        "extraction": "html",
        "categories": [
            ("https://shivangikooks.com/category/my-recipes/breakfast/", "Indian"),
            ("https://shivangikooks.com/category/my-recipes/lunch/", "Indian"),
            ("https://shivangikooks.com/category/my-recipes/dinner/", "Indian"),
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
    # ── The Burmalicious ──────────────────────────────────────────────────────
    # Squarespace site — no JSON-LD or recipe plugin. Recipes are plain HTML
    # with "Ingredients" heading and ul/li ingredient lists. Discovered via
    # flat sitemap; all posts live under /blog/[slug].
    "theburmalicious": {
        "name": "The Burmalicious",
        "discovery": "sitemap",
        "sitemap_index_url": "https://www.theburmalicious.com/sitemap.xml",
        "url_pattern": r"https://www\.theburmalicious\.com/blog/[^/]+$",
        "cuisine_default": "Burmese",
        "delay": 2.0,
        "extraction": "html",
    },
    # ── YouTube channels ──────────────────────────────────────────────────────
    # Add YouTube cooking channels here. Videos can be in any language —
    # Claude translates descriptions/transcripts to English during extraction.
    # Requires ANTHROPIC_API_KEY. Uses yt-dlp to fetch captions.
    #
    "phyu_home_cooking": {
        "name": "Phyu Home Cooking",
        "discovery": "youtube",
        "channel_url": "https://www.youtube.com/@phyuhomecooking/videos",
        "cuisine": "Burmese",
        "delay": 2.0,
        "max_videos": 100,
    },
    "spice_n_pans": {
        "name": "Spice N Pans",
        "discovery": "youtube",
        "channel_url": "https://www.youtube.com/@spicenpans/videos",
        "cuisine": "Singaporean",
        "extraction": "description",
        "delay": 0.5,
        "max_videos": 100,
    },
}

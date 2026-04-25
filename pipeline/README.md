# Recipe Extraction Pipeline

A modular pipeline for scraping recipe metadata from Asian food blogs and
producing the `app/recipes/data.py` corpus used by the app.

---

## Workflow

```
scrape → staging review → append to data.py
```

1. **Scrape** — fetches recipe pages, writes results to `pipeline/staging/<site>.py`

   ```bash
   uv run python pipeline/run.py --site rasa_malaysia
   ```

2. **Review** — open `pipeline/staging/rasa_malaysia.py`, delete bad entries

3. **Append** — copy approved dict blocks into `app/recipes/data.py`
   (the format is identical — no reformatting needed)

Staging files are gitignored so they don't pollute the repo.

---

## Extraction Approach

### Why JSON-LD?

Most food blogs publish [schema.org/Recipe](https://schema.org/Recipe)
structured data as a `<script type="application/ld+json">` block — required
for Google's rich recipe snippets. This is machine-written, stable across
layout redesigns, and gives us clean data without brittle HTML parsing.

Fields extracted from JSON-LD:

| Our field     | JSON-LD field                         | Notes                                 |
| ------------- | ------------------------------------- | ------------------------------------- |
| `name`        | `name`                                | Direct                                |
| `source_url`  | page URL                              | From discovery step                   |
| `source`      | site config                           | From `sites.py`                       |
| `cuisine`     | category URL                          | Assigned by discovery category        |
| `cook_time`   | `cookTime` → `totalTime` → `prepTime` | ISO 8601 → "30 min" / "1h 30min"      |
| `difficulty`  | inferred from `totalTime`             | ≤20min=Easy, ≤45min=Medium, else Hard |
| `ingredients` | `recipeIngredient[]`                  | Cleaned: quantities/units stripped    |

**Known limitations:**

- Difficulty is inferred from total time — a recipe with 20min cook + 4h marinade
  gets classified as Hard because the JSON-LD `totalTime` includes inactive waiting.
- Cuisine comes from the category URL the recipe was discovered under.

---

## URL Discovery

### Category crawl (default)

Crawls paginated listing pages (e.g. `/recipes/malaysian-recipes/`) and
collects all links that look like recipe slugs. WordPress blogs use
`/page/N/` pagination; the crawler stops when a page yields no new links.

Every URL found on `/recipes/malaysian-recipes/` is automatically labelled
`Malaysian` — cuisine assignment is a natural byproduct of the category.

### Sitemap walk (alternative)

For sites with a well-structured sitemap index: walk
`sitemap_index.xml` → sub-sitemaps → collect all post URLs.
Faster and more complete but doesn't carry cuisine info — pair with a
URL pattern map to assign cuisines.

---

## Handling Different Website Types

### Type 1: JSON-LD (most modern food blogs)

**How to check:** open DevTools → Elements → search `application/ld+json`.
If you see `"@type": "Recipe"`, this works out of the box.

**Examples:** Rasa Malaysia, The Woks of Life, Panlasang Pinoy, Hungry Huy.

**How to add:** just add an entry to `pipeline/sites.py` — no code changes.

### Type 2: HTML microdata (older blogs)

Some older WordPress sites use `itemprop` attributes in HTML instead of
(or alongside) JSON-LD:

```html
<span itemprop="cookTime" content="PT20M">20 minutes</span>
<span itemprop="recipeIngredient">2 tablespoons sesame oil</span>
```

**How to handle:** add a fallback extractor in `pipeline/extract.py`:

```python
def extract_from_microdata(html_text: str) -> Optional[dict]:
    # parse itemprop="recipeIngredient", itemprop="cookTime", etc.
    ...
```

Then call it in `map_to_recipe` when JSON-LD returns nothing.

### Type 3: Site-specific API or JSON endpoint

Some sites load recipes via a REST API or embed a JSON blob in a
`<script id="__NEXT_DATA__">` tag (Next.js sites) or
`window.__INITIAL_STATE__` (React/Redux).

**How to check:** open Network tab in DevTools, filter by XHR/Fetch,
reload the page and look for a JSON response containing ingredients.

**How to handle:** add a custom `discover_via_api()` function in
`pipeline/discover.py` and a matching extractor in `pipeline/extract.py`.

### Type 4: JavaScript-rendered pages

Some modern blogs render recipe content entirely in JavaScript — the raw
HTML contains no recipe data at all.

**Signs:** the page source (Ctrl+U) shows no ingredients but the browser
renders them fine. JSON-LD is absent. `<noscript>` tags everywhere.

**How to handle:** requires a headless browser (Playwright or Selenium).
This is out of scope for this stdlib-only pipeline. Options:

- Check if the site has a mobile version that serves plain HTML
- Check if the site has a printer-friendly URL that bypasses JS rendering
- Use Playwright in a separate `pipeline/browser.py` module:
  ```bash
  pip install playwright && playwright install chromium
  ```
  then `page.content()` gives you the rendered HTML to pass to `find_recipe_jsonld()`.

### Type 5: Recipe aggregators with their own schema

Sites like AllRecipes, Food Network, or Epicurious have large recipe databases
but may throttle aggressively or prohibit scraping in their ToS.
**Always check `robots.txt` and ToS before adding a new site.**

---

## Module Overview

```
pipeline/
├── sites.py          Config per source site (discovery, cuisines, delay)
├── fetch.py          HTTP layer (rate limiting, exponential backoff retry)
├── discover.py       URL discovery (category crawl + sitemap walk)
├── extract.py        JSON-LD parsing and field mapping
├── transform.py      Ingredient cleaning, time formatting, difficulty inference
├── store.py          JSONL cache + staging writer + data.py emitter
├── run.py            CLI entry point
└── pyproject.toml    Standalone project for GitHub Actions / containerised use
```

---

## CLI Reference

```bash
# List configured sites
uv run python pipeline/run.py --list-sites

# Discover URLs only (no recipe pages fetched)
uv run python pipeline/run.py --site rasa_malaysia --discover-only

# Scrape up to 10 new recipes (skips cached URLs)
uv run python pipeline/run.py --site rasa_malaysia --limit 10

# Full incremental run (cached URLs skipped, staging written on completion)
uv run python pipeline/run.py --site rasa_malaysia

# Force full re-scrape (clears cache first)
uv run python pipeline/run.py --site rasa_malaysia --no-cache

# Scrape without writing staging file
uv run python pipeline/run.py --site rasa_malaysia --no-staging

# Regenerate data.py from all cached recipes (bypasses staging)
uv run python pipeline/run.py --from-cache --output app/recipes/data.py

# Verify generated data.py is valid Python
python -c "from app.recipes.data import RECIPES; print(len(RECIPES), 'recipes')"
```

---

## Running in GitHub Actions

The pipeline has its own `pyproject.toml` with no external dependencies (stdlib only),
so it can run in a minimal Python environment.

```yaml
- uses: astral-sh/setup-uv@v4
  with:
    python-version: "3.12"
- run: uv run python pipeline/run.py --site rasa_malaysia --limit 50
- uses: actions/upload-artifact@v4
  with:
    name: staging
    path: pipeline/staging/
```

See `.github/workflows/scrape-recipes.yml` for a full workflow with
`workflow_dispatch` inputs (site, limit) that can be triggered manually from
the GitHub Actions UI.

---

## Cache Format

`pipeline/cache/<site_key>.jsonl` — one JSON object per line:

```json
{
  "id": "sesame-oil-chicken",
  "name": "Sesame Oil Chicken",
  "source": "Rasa Malaysia",
  "source_url": "https://rasamalaysia.com/recipe-sesame-oil-chicken/",
  "cuisine": "Malaysian",
  "cook_time": "20 min",
  "difficulty": "Easy",
  "ingredients": ["chicken", "sesame oil", "ginger", "soy sauce"]
}
```

Append-only. Use `--no-cache` to rebuild from scratch.
Both `cache/` and `staging/` are gitignored.

---

## Adding a New Site

1. **Verify JSON-LD** — open a recipe page source, search `application/ld+json`.

2. **Find category URLs** — confirm pagination works (`/page/2/`).

3. **Add to `pipeline/sites.py`**:

   ```python
   "my_site": {
       "name": "My Site",
       "discovery": "category",
       "delay": 2.0,
       "max_pages": 5,
       "categories": [
           ("https://mysite.com/recipes/vietnamese/", "Vietnamese"),
       ],
   },
   ```

4. **Test discovery:**

   ```bash
   uv run python pipeline/run.py --site my_site --discover-only
   ```

5. **Test extraction:**
   ```bash
   uv run python pipeline/run.py --site my_site --limit 3
   cat pipeline/cache/my_site.jsonl | python -m json.tool
   ```

---

## Ingredient Cleaning

`transform.clean_ingredient()` normalises each ingredient string:

1. Strip parenthetical notes: `"chicken (boneless)"` → `"chicken"`
2. Strip quantity + unit: `"2 tbsp sesame oil"` → `"sesame oil"`
3. Handle modifiers: `"¼ heaping teaspoon turmeric"` → `"turmeric"`
4. Strip leading numbers: `"3 spring onions"` → `"spring onions"`
5. Lowercase and collapse whitespace

The goal is a bare ingredient name for matching against a user's pantry.

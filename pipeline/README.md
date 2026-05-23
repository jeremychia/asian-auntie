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

2. **Review** — open `pipeline/staging/rasa_malaysia.py`, clean and correct entries
   (see [Staging Review Guide](#staging-review-guide) below)

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

### Type 2: Plain HTML — no recipe plugin

Some WordPress food blogs (e.g. Shivangi Kooks) write recipe content directly
in the post body without a recipe plugin. There is no JSON-LD and no
`itemprop` markup — ingredients live in a plain `<ul>/<li>` list after an
"Ingredients" heading.

**How to check:** open page source (Ctrl+U) and search for `"@type": "Recipe"`
(JSON-LD) and `wprm-recipe-ingredient` (WP Recipe Maker). If neither is
present but you can see an `<h3>Ingredients</h3>` followed by a `<ul>`, use
this extraction mode.

**How to add:**

```python
"my_site": {
    "name": "My Site",
    "discovery": "category",
    "delay": 2.0,
    "max_pages": 3,
    "extraction": "html",           # ← triggers heading-based HTML extraction
    "categories": [
        ("https://mysite.com/category/lunch/", "Indian"),
    ],
},
```

**How it works:** `find_recipe_html()` in `extract.py` opens an "ingredient
section" when it sees a short heading (≤ 40 chars) containing "ingredient",
collects all `<ul>/<li>` blocks until an "Instructions" heading closes the
section, then picks the blocks that score ≥ 60% ingredient-like items.
Sub-section headings (Dough / Filling / Sauce) are ignored — they don't close
the section. Cook time is scraped from labeled text near "cook time:" or
"total time:" labels.

**Limitations:** depends on consistent heading names. If the site uses "What
you'll need" instead of "Ingredients", or instructions under "Method" not
"Instructions", you may need to extend `_is_ingredient_heading()` or
`_INSTRUCTIONS_RE` in `extract.py`.

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

### Step 1 — identify the extraction type

Open a recipe page source and search for:

| What you find                                                    | Extraction type                             |
| ---------------------------------------------------------------- | ------------------------------------------- |
| `"@type": "Recipe"` inside `<script type="application/ld+json">` | JSON-LD (default)                           |
| `<script id="__NEXT_DATA__">`                                    | Next.js (`"extraction": "nextdata"`)        |
| `wprm-recipe-ingredient` class names                             | WP Recipe Maker — handled by HTML extractor |
| `<h3>Ingredients</h3>` + plain `<ul>`                            | Plain HTML (`"extraction": "html"`)         |

### Step 2 — find category or sitemap URLs

For category discovery: confirm WordPress pagination works (`/page/2/`).
For sitemap discovery: check `https://<domain>/sitemap.xml`.

### Step 3 — add to `pipeline/sites.py`

**JSON-LD site (most common):**

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

**Plain-HTML site (no recipe plugin):**

```python
"my_site": {
    "name": "My Site",
    "discovery": "category",
    "delay": 2.0,
    "max_pages": 3,
    "extraction": "html",
    "categories": [
        ("https://mysite.com/category/lunch/", "Indian"),
        ("https://mysite.com/category/dinner/", "Indian"),
    ],
},
```

### Step 4 — test discovery

```bash
uv run python pipeline/run.py --site my_site --discover-only
```

### Step 5 — test extraction on a small batch

```bash
uv run python pipeline/run.py --site my_site --limit 5
```

Open `pipeline/staging/<date>_my_site.py` and check:

- Ingredient lists look clean (no nav links, no prose paragraphs)
- `normalized_ingredients` maps PANTRY_ITEMS correctly (soy sauce → Dark soy sauce etc.)
- `cook_time` is populated (or "unknown" for recipes without explicit timing)

### Step 6 — full scrape and import

```bash
# Full scrape (cached URLs are skipped on subsequent runs)
uv run python pipeline/run.py --site my_site

# Review pipeline/staging/<date>_my_site.py — delete bad entries

# Copy approved dict blocks directly into app/recipes/data.py
# (format is identical — no reformatting needed)
```

### Step 7 — update the frontend filter dropdowns

`templates/recipes/index.html` contains two hard-coded `<select>` dropdowns that
must be kept in sync with `pipeline/sites.py` and `app/recipes/data.py`:

- **Website filter** (`#website-filter`) — add an `<option>` for each new `name`
  value (the display name from `sites.py`).
- **Cuisine filter** (`#cuisine-filter`) — add an `<option>` if the cuisine label
  is not already listed.

Both lists are alphabetically ordered — insert the new entry in the right place.

---

## Ingredient Cleaning

There are two cleaning stages, applied in sequence.

### Stage 1 — `transform.clean_ingredient()` (stored in `recipe["ingredients"]`)

Produces a human-readable ingredient name, retaining preparation context:

1. Strip leading `+` (used by some blogs as "extra/optional" marker)
2. Strip parenthetical notes: `"chicken (boneless)"` → `"chicken"`
3. Strip quantity + unit: `"2 tbsp sesame oil"` → `"sesame oil"`
   - Unit word-boundary check prevents `g` stripping the first letter of "garlic"
4. Strip leading bare numbers: `"3 spring onions"` → `"spring onions"`
5. Lowercase and collapse whitespace

Result: `"garlic, chopped"`, `"sesame seeds"`, `"uncooked whole wheat noodles"`.

### Stage 2 — `store._pre_normalize()` (stored in `recipe["normalized_ingredients"]`)

Applied before PANTRY_ITEMS lookup; produces a simplified form for matching:

1. Strip everything after the first comma: `"garlic, chopped"` → `"garlic"`
2. Strip trailing qualifiers: `"pasta of your choice"` → `"pasta"`,
   `"salt to taste"` → `"salt"`, `"water as needed"` → `"water"`
3. Strip leading state adjectives: `"uncooked whole wheat noodles"` → `"whole wheat noodles"`,
   `"boiled potato"` → `"potato"`
4. Map to a canonical PANTRY_ITEMS entry via `normalize_ingredient()` — bidirectional
   substring + subsequence matching, so both `"soy sauce"` → `"Dark soy sauce"` and
   `"gochujang paste"` → `"Gochujang"` resolve correctly
5. Fall back to the pre-normalized string if no PANTRY_ITEMS entry matches

Result: `"garlic"`, `"Sesame seeds"`, `"whole wheat noodles"`.

---

## Staging Review Guide

The scraper produces a good first pass, but staging files always need a human review before being merged into `app/recipes/data.py`. Work through each recipe dict and apply the rules below.

### 1. `id` and `name`

YouTube channel titles in particular are written for SEO and clicks. Strip everything that isn't the dish name:

- Remove Chinese characters
- Remove sensational prefixes/suffixes: "Secret Tip for…", "…Chinese Dim Sum Seafood Meat Roll Recipe", "How to Make…", "The BEST…"
- Keep only the core dish name, sentence-case, lowercase
- Derive `id` as the kebab-case version of the cleaned `name`

```python
# Before
"id": "secret-tip-for-bouncy-beancurd-rolls-in-oyster-sauce-...",
"name": "Secret Tip for Bouncy Beancurd Rolls in Oyster Sauce 蚝油腐皮卷 Chinese Dim Sum",

# After
"id": "beancurd-rolls-in-oyster-sauce",
"name": "Beancurd rolls in oyster sauce",
```

### 2. `cuisine`

The scraper assigns cuisine from the category URL, which is often wrong for channels that cover multiple cuisines. Look at the dish name and correct accordingly:

| Dish clue                                                                                                         | Cuisine     |
| ----------------------------------------------------------------------------------------------------------------- | ----------- |
| Korean dish names (bibimbap, doenjang jjigae, kimchi jjigae, tteokbokki, japchae, galbi, samgyeopsal, yukgaejang) | Korean      |
| Japanese dish names (ramen, tonkotsu, miso, teriyaki, gyoza, karaage, okonomiyaki, takoyaki)                      | Japanese    |
| Malaysian dishes (rendang, laksa, nasi lemak, char kway teow)                                                     | Malaysian   |
| Taiwanese dishes (three-cup chicken, lu rou fan)                                                                  | Taiwanese   |
| Vietnamese dishes (pho, bun bo hue, banh mi)                                                                      | Vietnamese  |
| Sichuan, Cantonese, Hakka, Shanghainese, Teochew dishes                                                           | Chinese     |
| Fusion or expat adaptations with Western base                                                                     | Western     |
| Default for Singaporean hawker dishes                                                                             | Singaporean |

### 3. `normalized_ingredients`

This is the field the app uses for recipe matching — it must contain only clean, canonical ingredient names. The scraper's normalization pipeline has several known failure modes:

#### Remove pipeline artifacts

These appear when the scraper picks up non-ingredient content from the page:

- Section headers: `"Main ingredients:"`, `"For the sauce:"`, `"Marinate:"`, `"Batter:"`, `"Soup base:"`, `"For stir-frying:"`, `"To clean the ribs:"`, `"Pre-prepared ingredients:"`
- Separator lines: `"——"`, `"==="`, `"---"`, `"* * *"`
- Empty strings `""`
- Amazon affiliate or any other URLs: `"cooking oil https://amzn.to/..."`
- Timing tables or any multi-column text that ended up as a list item

#### Fix wrong PANTRY_ITEMS mappings

The normalizer uses substring/subsequence matching, which misfires on compound phrases. Always check:

| Wrong                            | Correct                                      | Trigger phrase                             |
| -------------------------------- | -------------------------------------------- | ------------------------------------------ |
| `"Shallots"` (when not shallots) | remove or `"Salt"`                           | `"salt"` matched via subsequence           |
| `"Butter"`                       | remove                                       | `"butterflied"`                            |
| `"Water chestnuts"`              | `"Chestnuts"`                                | `"chestnuts, peeled"`                      |
| `"Mustard"`                      | `"Pickled mustard greens"`                   | `"sour pickled mustard greens"`            |
| `"Tamari"`                       | `"Tamarind"`                                 | `"asam or tamarind water"`                 |
| `"Beef"`                         | `"Beef stock"`                               | `"beef stock"`                             |
| `"Glutinous rice"`               | `"Rice wine"`                                | `"hakka glutinous rice wine"`              |
| `"Sugar"`                        | `"Sugar snap peas"`                          | `"sugar snap peas"`                        |
| `"Potato"`                       | `"Sweet potato starch"` or `"Potato starch"` | `"sweet potato flour"` / `"potato starch"` |
| `"Onion"`                        | `"Spring onions"`                            | `"spring onion stem"`                      |

If you spot a new pattern, add it to this table.

#### Normalize descriptive forms

Ingredients should be the ingredient, not a preparation note:

| Before                          | After             |
| ------------------------------- | ----------------- |
| `"a little cornflour slurry"`   | `"Cornflour"`     |
| `"cornflour solution"`          | `"Cornflour"`     |
| `"cornstarch solution"`         | `"Cornflour"`     |
| `"a handful of leafy greens"`   | `"Leafy greens"`  |
| `"scallion"` / `"scallions"`    | `"Spring onions"` |
| `"green, yellow or red pepper"` | `"Bell pepper"`   |
| `"* 350g fish"`                 | `"Fish"`          |

#### Remove non-pantry items

- **Water** — not a pantry tracking item; remove it
- Plain quantities like `"2.5l"` or bare numbers that slipped through

#### Check for duplicates

Duplicates within a single recipe's `normalized_ingredients` add no value and slightly inflate the match %. Remove them.

### 4. Validation

After cleaning, run a quick sanity check:

```python
python3 -c "
with open('pipeline/staging/<date>_<site>.py') as f:
    exec(f.read())
issues = []
for r in RECIPES:
    for ing in r.get('normalized_ingredients', []):
        ing_lower = ing.lower()
        if any(x in ing_lower for x in ['slurry', 'solution', 'http', 'method', 'ingredient', 'batter', 'marinate']):
            issues.append((r['id'], ing))
        if not ing.strip() or ing[0].isdigit():
            issues.append((r['id'], repr(ing)))
for rid, ing in issues:
    print(f'{rid}: {ing}')
print(f'Total: {len(RECIPES)} recipes, {len(issues)} issues')
"
```

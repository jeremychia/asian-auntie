"""
Intermediate JSONL cache, staging files, and final data.py output.

Cache format
------------
One JSON object per line in pipeline/cache/<site_key>.jsonl.
Each line is a complete recipe dict as returned by extract.map_to_recipe().
The cache lets you resume interrupted runs and avoid re-fetching.

Staging
-------
After scraping, results land in pipeline/staging/<site_key>.py — a human-
readable Python file in exactly the same format as app/recipes/data.py.
A reviewer inspects it, removes bad entries, and appends the remainder to
app/recipes/data.py. Because the format is identical, appending is just
copying the dict blocks (no reformatting needed).
"""

import re
import json
import datetime
import pathlib
from collections import defaultdict
from typing import Optional

_TRAILING_NOISE_RE = re.compile(
    r"\s+(of your choice|to taste|as needed|as required|if needed|if required"
    r"|or as required|or as needed|adjust accordingly|to serve)\s*$",
    re.IGNORECASE,
)
_LEADING_STATE_RE = re.compile(
    r"^(uncooked|cooked|raw|boiled|steamed)\s+",
    re.IGNORECASE,
)

_CACHE_DIR = pathlib.Path(__file__).parent / "cache"
_STAGING_DIR = pathlib.Path(__file__).parent / "staging"


def cache_path(site_key: str) -> pathlib.Path:
    return _CACHE_DIR / f"{site_key}.jsonl"


def load_cache(site_key: str) -> dict[str, dict]:
    """Return {source_url: recipe} for all recipes already in cache."""
    path = cache_path(site_key)
    if not path.exists():
        return {}
    recipes: dict[str, dict] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                recipes[r["source_url"]] = r
            except (json.JSONDecodeError, KeyError):
                continue
    return recipes


def append_to_cache(site_key: str, recipe: dict) -> None:
    """Append a single recipe to the JSONL cache file."""
    _CACHE_DIR.mkdir(exist_ok=True)
    with cache_path(site_key).open("a") as f:
        f.write(json.dumps(recipe, ensure_ascii=False) + "\n")


def clear_cache(site_key: str) -> None:
    path = cache_path(site_key)
    if path.exists():
        path.unlink()


def load_all_caches() -> list[dict]:
    """Load every cached recipe across all sites, deduplicating by recipe id."""
    seen_ids: set[str] = set()
    recipes: list[dict] = []
    for jsonl_file in sorted(_CACHE_DIR.glob("*.jsonl")):
        with jsonl_file.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("id") not in seen_ids:
                    seen_ids.add(r["id"])
                    recipes.append(r)
    return recipes


# ── data.py output ────────────────────────────────────────────────────────────

_CUISINE_ORDER = [
    "Malaysian",
    "Thai",
    "Filipino",
    "Indonesian",
    "Vietnamese",
    "Singaporean",
    "Chinese",
]


def _repr_list(items: list[str], indent: int) -> str:
    pad = " " * indent
    inner = (",\n" + pad + "    ").join(f'"{i}"' for i in items)
    return f"[\n{pad}    {inner},\n{pad}]"


def staging_path(site_key: str) -> pathlib.Path:
    today = datetime.date.today().isoformat()
    return _STAGING_DIR / f"{today}_{site_key}.py"


def write_staging(site_key: str, recipes: list[dict]) -> pathlib.Path:
    """Write recipes to pipeline/staging/<site_key>.py for human review.

    The file is in exactly the same format as app/recipes/data.py so that
    approved entries can be copy-pasted directly into RECIPES without reformatting.
    """
    _STAGING_DIR.mkdir(exist_ok=True)
    path = staging_path(site_key)
    content = emit_data_py(recipes, source=f"pipeline/run.py --site {site_key}")
    # Replace the module-level header with a staging header so the reviewer
    # knows this file is NOT the live data and should not be imported directly.
    content = content.replace(
        "# Curated Malaysian and Southeast Asian recipe corpus.",
        "# STAGING — review before adding to app/recipes/data.py.",
    )
    path.write_text(content)
    return path


def _pre_normalize(text: str) -> str:
    """Simplify a cleaned ingredient string before PANTRY_ITEMS lookup.

    Strips preparation notes and trailing qualifiers so that e.g.
    "uncooked whole wheat noodles" → "whole wheat noodles" and
    "pasta of your choice" → "pasta". The original text is kept in
    recipe["ingredients"]; this simplified form is used only for
    normalized_ingredients.
    """
    text = text.strip()
    text = re.sub(r",.*$", "", text)  # strip after first comma
    text = _TRAILING_NOISE_RE.sub("", text)  # strip "of your choice" etc.
    text = _LEADING_STATE_RE.sub("", text)  # strip "uncooked", "boiled" etc.
    return text.strip()


def _normalize_ingredients(raw_ingredients: list[str]) -> list[str]:
    """Return canonical normalized form of each ingredient using the pantry map."""
    from app.ingredient_normalization import normalize_ingredient

    result = []
    for i in raw_ingredients:
        pre = _pre_normalize(i)
        normalized = normalize_ingredient(pre)
        result.append(normalized or pre.lower())
    return result


def emit_data_py(recipes: list[dict], source: Optional[str] = None) -> str:
    """Render a list of recipe dicts as a valid app/recipes/data.py file."""
    source_note = source or "scripts/pipeline/run.py"
    lines = [
        "# Curated Malaysian and Southeast Asian recipe corpus.",
        "# Instructions are never stored here — we only hold enough metadata to compute",
        "# ingredient match % and link to the source.",
        f"# Generated by {source_note} — do not edit by hand.",
        "",
        "RECIPES = [",
    ]

    by_cuisine: dict[str, list[dict]] = defaultdict(list)
    for r in recipes:
        by_cuisine[r["cuisine"]].append(r)

    ordered = _CUISINE_ORDER + [
        c for c in sorted(by_cuisine) if c not in _CUISINE_ORDER
    ]

    for cuisine in ordered:
        if cuisine not in by_cuisine:
            continue
        lines.append(f"    # ── {cuisine} {'─' * (73 - len(cuisine))}")
        for r in by_cuisine[cuisine]:
            normalized = r.get(
                "normalized_ingredients",
                _normalize_ingredients(r["ingredients"]),
            )
            lines.append("    {")
            lines.append(f'        "id": "{r["id"]}",')
            lines.append(f'        "name": "{r["name"]}",')
            lines.append(f'        "source": "{r["source"]}",')
            lines.append(f'        "source_url": "{r["source_url"]}",')
            lines.append(f'        "cuisine": "{r["cuisine"]}",')
            lines.append(f'        "cook_time": "{r["cook_time"]}",')
            lines.append(f'        "difficulty": "{r["difficulty"]}",')
            lines.append(
                f'        "ingredients": {_repr_list(r["ingredients"], indent=8)},'
            )
            lines.append(
                f'        "normalized_ingredients": {_repr_list(normalized, indent=8)},'
            )
            lines.append("    },")

    lines.append("]")
    lines.append("")
    return "\n".join(lines)

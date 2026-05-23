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
from functools import cache
from typing import Optional

_TRAILING_NOISE_RE = re.compile(
    r"\s+(of your choice|to taste|as needed|as required|if needed|if required"
    r"|or as required|or as needed|adjust accordingly|to serve)\s*$",
    re.IGNORECASE,
)
_LEADING_STATE_RE = re.compile(
    r"^(uncooked|cooked|raw|boiled|steamed"
    r"|bone-?in|boneless|skin-?on|skin-?off|skinless|free-?range)\s+",
    re.IGNORECASE,
)
_COMPOUND_ADJECTIVE_RE = re.compile(r"^\w+-\w+$")
_STANDALONE_QUALIFIER_RE = re.compile(
    r"^(large|medium|small|big|whole|ripe)s?$", re.IGNORECASE
)
_OR_FRAGMENT_RE = re.compile(r"^(or|and|to)\b", re.IGNORECASE)

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
    if not items:
        return "[]"
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
    # Drop "or …" / "and …" fragments that are site copy artifacts, not ingredients.
    if _OR_FRAGMENT_RE.match(text):
        return ""
    comma_idx = text.find(",")
    if comma_idx != -1:
        pre = text[:comma_idx].strip()
        # If the pre-comma segment is a compound adjective ("skin-on", "bone-in")
        # or a bare size/state qualifier ("large", "whole"), the real ingredient
        # name follows the comma — take the last segment instead of the first.
        if _COMPOUND_ADJECTIVE_RE.match(pre) or _STANDALONE_QUALIFIER_RE.match(pre):
            text = text.rsplit(",", 1)[-1].strip()
        else:
            text = pre
    text = _TRAILING_NOISE_RE.sub("", text)  # strip "of your choice" etc.
    prev = None
    while (
        text != prev
    ):  # strip stacked leading adjectives: "bone-in free-range chicken" → "chicken"
        prev = text
        text = _LEADING_STATE_RE.sub("", text)
    return text.strip()


@cache
def _load_pantry_items() -> tuple[str, ...]:
    """Load PANTRY_ITEMS directly from app/pantry_data.py via importlib.

    Uses importlib to bypass app/__init__.py (which imports Flask, unavailable
    in the pipeline env). Result is cached so the file is only read once.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_pipeline_pantry_data",
        pathlib.Path(__file__).parent.parent / "app" / "pantry_data.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return tuple(mod.PANTRY_ITEMS)


def _normalize_ingredient(name: str, pantry_items: tuple[str, ...]) -> str | None:
    """Subsequence-match name against pantry_items; return best match or None."""
    if not name:
        return None
    q = name.lower().strip()

    def score(candidate: str) -> float:
        s = candidate.lower()
        if q in s:
            coverage = len(q) / len(s)
            return (100 + coverage * 10) if coverage >= 0.55 else 0
        if s in q:
            return 100 + len(s) / len(q) * 10
        shorter, longer = (q, s) if len(q) <= len(s) else (s, q)
        if len(shorter) / len(longer) < 0.5:
            return 0
        j = 0
        for ch in longer:
            if j < len(shorter) and ch == shorter[j]:
                j += 1
        return (10 + len(shorter) / len(longer) * 10) if j == len(shorter) else 0

    best_score, best_item = max(
        ((score(item), item) for item in pantry_items), key=lambda x: x[0]
    )
    return best_item if best_score > 0 else None


def _normalize_ingredients(raw_ingredients: list[str]) -> list[str]:
    """Return canonical normalized form of each ingredient using the pantry map."""
    pantry_items = _load_pantry_items()
    result = []
    for i in raw_ingredients:
        pre = _pre_normalize(i)
        normalized = _normalize_ingredient(pre, pantry_items)
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

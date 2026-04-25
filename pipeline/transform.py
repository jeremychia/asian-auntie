"""
Data cleaning and normalisation functions.

These are pure functions with no I/O — safe to unit test in isolation.
"""

import re
from typing import Optional


def clean_ingredient(text: str) -> str:
    """Strip quantities, units, and parenthetical notes; normalise to lowercase."""
    text = text.strip()
    text = re.sub(r"\s*\(.*?\)", "", text)
    text = re.sub(
        r"^[\d½¼¾⅓⅔⅛⅜⅝⅞⅙⅚⅕⅖⅗⅘\s/–-]+\s*"
        r"(?:heaping\s+|level\s+|rounded\s+)?"
        r"(?:cup|tbsp|tsp|tablespoon|teaspoon|pound|lb|oz|g|gram|kg|ml|l|liter|litre"
        r"|piece|clove|stalk|bunch|handful|pinch|dash|sprig|head|slice|sheet"
        r"|can|tin|package|pkg|bag|bottle|jar|drop|quart|pint)s?"
        r"(?:\s+of)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^[\d][\d\s–-]*\s+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def parse_duration_minutes(iso: Optional[str]) -> Optional[int]:
    """Parse ISO 8601 duration string (PT45M, PT1H30M) to total minutes."""
    if not iso:
        return None
    # Search for H and M components separately — a combined optional regex
    # matches empty string at position 0 before reaching the digits.
    h = re.search(r"(\d+)H", iso)
    m = re.search(r"(\d+)M", iso)
    if not h and not m:
        return None
    hours = int(h.group(1)) if h else 0
    mins = int(m.group(1)) if m else 0
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
    """Infer difficulty from total cook time. Recipes don't publish difficulty ratings."""
    if not total_minutes:
        return "Medium"
    if total_minutes <= 20:
        return "Easy"
    if total_minutes <= 45:
        return "Medium"
    return "Hard"


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")

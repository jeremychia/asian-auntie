"""Ingredient normalization — maps raw names to canonical pantry items."""

from app.perishables.forms import PANTRY_ITEMS


def normalize_ingredient(name: str) -> str | None:
    """Return the best-matching PANTRY_ITEMS entry for a given name, or None.

    Uses character-level subsequence matching. Requires score > 0 and picks
    the highest scorer.
    """
    if not name:
        return None
    q = name.lower().strip()

    def score(candidate: str) -> float:
        s = candidate.lower()
        if q in s:
            return 100 + len(q) / len(s) * 10
        j = 0
        for ch in s:
            if j < len(q) and ch == q[j]:
                j += 1
        return (10 + len(q) / len(s) * 10) if j == len(q) else 0

    scored = [(score(item), item) for item in PANTRY_ITEMS]
    best_score, best_item = max(scored, key=lambda x: x[0])
    return best_item if best_score > 0 else None

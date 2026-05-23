"""Ingredient normalization — maps raw names to canonical pantry items."""

from functools import lru_cache

from app.pantry_data import PANTRY_ITEMS


@lru_cache(maxsize=512)
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
            # raw is a substring of the PANTRY_ITEM — require it covers ≥ 55% of
            # the candidate so "water" doesn't match "Water chestnuts" and
            # "mushrooms" doesn't match "Wood ear mushrooms"
            coverage = len(q) / len(s)
            return (100 + coverage * 10) if coverage >= 0.55 else 0
        if s in q:
            # PANTRY_ITEM is a substring of the raw ingredient (e.g. "gochugaru"
            # inside "chilli powder/gochugaru, adjust accordingly") — always accept
            return 100 + len(s) / len(q) * 10
        # Subsequence: shorter must be ≥ 50% of the longer to avoid spurious matches
        # ("pasta" ⊂ "potato starch" scores 0 because 5/13 < 0.5)
        shorter, longer = (q, s) if len(q) <= len(s) else (s, q)
        if len(shorter) / len(longer) < 0.5:
            return 0
        j = 0
        for ch in longer:
            if j < len(shorter) and ch == shorter[j]:
                j += 1
        return (10 + len(shorter) / len(longer) * 10) if j == len(shorter) else 0

    scored = [(score(item), item) for item in PANTRY_ITEMS]
    best_score, best_item = max(scored, key=lambda x: x[0])
    return best_item if best_score > 0 else None

import re
from collections import defaultdict

from app.ingredient_normalization import normalize_ingredient
from app.perishables.forms import PANTRY_ITEMS
from app.recipes.data import RECIPES


def parse_cook_time(cook_time_str: str) -> int | None:
    """Parse cook time string (e.g. '15 min', '1 hour 30 min') to minutes.
    Returns None if parsing fails.
    """
    if not cook_time_str or not isinstance(cook_time_str, str):
        return None

    cook_time_str = cook_time_str.lower().strip()
    total_minutes = 0

    hours_match = re.search(r"(\d+)\s*(?:hour|hr)", cook_time_str)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60

    mins_match = re.search(r"(\d+)\s*(?:min|minute)", cook_time_str)
    if mins_match:
        total_minutes += int(mins_match.group(1))

    return total_minutes if total_minutes > 0 else None


_STOP_WORDS = {
    "a",
    "an",
    "the",
    "of",
    "with",
    "and",
    "or",
    "in",
    "for",
    "to",
    "sauce",
    "paste",
    "powder",
    "ground",
    "fresh",
    "dried",
    "sliced",
    "chopped",
    "whole",
    "boneless",
    "skinless",
    "raw",
}

# Curated synonym map: user-typed alias → recipe ingredient term(s) it should match.
# Keep entries lowercase. Expand as zero-result searches are observed in the wild.
SYNONYMS: dict[str, list[str]] = {
    # Fish sauce aliases
    "nam pla": ["fish sauce"],
    "patis": ["fish sauce"],
    # Soy sauce variants
    "light soy": ["light soy sauce"],
    "dark soy": ["dark soy sauce"],
    "sweet soy": ["sweet soy sauce"],
    "kecap manis": ["sweet soy sauce"],
    "kicap manis": ["sweet soy sauce"],
    # Shrimp paste aliases
    "blachan": ["belacan"],
    "blachan paste": ["belacan"],
    "trassi": ["belacan"],
    "shrimp paste": ["belacan"],
    "bagoong": ["belacan", "shrimp paste"],
    # Palm / coconut sugar aliases
    "gula melaka": ["palm sugar"],
    "coconut sugar": ["palm sugar"],
    "jaggery": ["palm sugar"],
    # Lemongrass
    "lemon grass": ["lemongrass"],
    "serai": ["lemongrass"],
    # Galangal
    "blue ginger": ["galangal"],
    "lengkuas": ["galangal"],
    # Kaffir lime leaves
    "makrut lime leaves": ["kaffir lime leaves"],
    "makrut lime": ["kaffir lime leaves"],
    "daun limau purut": ["kaffir lime leaves"],
    # Tamarind
    "tamarind paste": ["tamarind"],
    "tamarind juice": ["tamarind"],
    "asam": ["tamarind"],
    "asam jawa": ["tamarind"],
    # Coriander / cilantro — recipes use "cilantro"; map the English name to it
    "coriander": ["cilantro"],
    "coriander leaves": ["cilantro"],
    # Spring onions
    "scallions": ["spring onions"],
    "green onions": ["spring onions"],
    # Bok choy
    "pak choi": ["bok choy"],
    "pak choy": ["bok choy"],
    "bak choi": ["bok choy"],
    # Chinese broccoli
    "gai lan": ["chinese broccoli"],
    "kailan": ["chinese broccoli"],
    "choy sum": ["chinese broccoli"],
    # Kangkung
    "water spinach": ["kangkung"],
    "morning glory": ["kangkung"],
    "water morning glory": ["kangkung"],
    # Doubanjiang
    "toban djan": ["doubanjiang"],
    "chilli bean paste": ["doubanjiang"],
    "bean paste": ["doubanjiang"],
    # Dried shrimp
    "dried prawns": ["dried shrimp"],
    # Generic protein expansions (singular → plural)
    "prawn": ["prawns"],
    "shrimp": ["prawns"],
    "egg": ["eggs"],
    # Oil aliases (map to generic "oil" so recipes still match)
    "vegetable oil": ["oil"],
    "cooking oil": ["oil"],
    "sunflower oil": ["oil"],
    "peanut oil": ["oil"],
    "canola oil": ["oil"],
    # Chilli variants
    "chili": ["chillies"],
    "chile": ["chillies"],
    "hot pepper": ["chillies"],
    "dried chili": ["dried chillies"],
    # Tofu aliases
    "beancurd": ["tofu"],
    "bean curd": ["tofu"],
    "tofu puff": ["tofu"],
    # Cornstarch
    "corn starch": ["cornstarch"],
    "corn flour": ["cornstarch"],
    # Tapioca
    "tapioca flour": ["tapioca starch"],
    # General flour
    "plain flour": ["flour"],
    "all purpose flour": ["flour"],
}


def _words(text: str) -> frozenset[str]:
    tokens = re.sub(r"[^a-z\s]", "", text.lower()).split()
    return frozenset(t for t in tokens if t not in _STOP_WORDS and len(t) > 1)


_PANTRY_LOWER: frozenset[str] = frozenset(p.lower() for p in PANTRY_ITEMS)

# Pre-computed at module load from data.py's normalized_ingredients.
# Each entry: list of (raw_ingredient, normalized_lower, word_frozenset).
_RECIPE_INGREDIENTS: list[list[tuple[str, str, frozenset[str]]]] = []

# Inverted index: token → set of recipe indices with that token.
_INGREDIENT_INDEX: dict[str, set[int]] = defaultdict(set)

# Recipe ID → index into RECIPES (and _RECIPE_INGREDIENTS).
_RECIPE_ID_TO_IDX: dict[str, int] = {}


def _build_index() -> None:
    for idx, recipe in enumerate(RECIPES):
        _RECIPE_ID_TO_IDX[recipe["id"]] = idx

        raw_ings = recipe["ingredients"]
        pre_normalized = recipe.get("normalized_ingredients")

        ing_data: list[tuple[str, str, frozenset[str]]] = []
        if pre_normalized:
            # normalized_ingredients is a standalone canonical list, not 1-to-1
            # with raw ingredients (trivial items like water/salt are dropped).
            # Use normalized names for both matching and display.
            for norm in pre_normalized:
                norm_lower = norm.lower().strip()
                words = _words(norm_lower)
                ing_data.append((norm, norm_lower, words))
                _INGREDIENT_INDEX[norm_lower].add(idx)
                for word in words:
                    _INGREDIENT_INDEX[word].add(idx)
        else:
            # No pre-normalized list: normalize each raw ingredient 1-to-1.
            for raw in raw_ings:
                norm = normalize_ingredient(raw) or raw
                norm_lower = norm.lower().strip()
                words = _words(norm_lower)
                ing_data.append((raw, norm_lower, words))
                _INGREDIENT_INDEX[norm_lower].add(idx)
                for word in words:
                    _INGREDIENT_INDEX[word].add(idx)

        _RECIPE_INGREDIENTS.append(ing_data)


_build_index()


def _normalize_user(ui: str) -> str:
    """Normalize a single user ingredient, preserving SYNONYMS alias keys as-is.

    normalize_ingredient uses subsequence matching which mis-maps short alias words
    (e.g. 'shrimp' → 'Dried shrimp', 'egg' → 'Egg noodles') before SYNONYMS can run.
    Checking SYNONYMS first ensures aliases like 'shrimp' → ['prawns'] always fire.
    """
    raw_lower = ui.lower().strip()
    if raw_lower in SYNONYMS:
        return raw_lower
    return (normalize_ingredient(ui) or ui).lower().strip()


def candidate_recipe_indices(user_ingredients: list[str]) -> set[int]:
    """Return indices of recipes sharing at least one ingredient token with the user's list."""
    candidates: set[int] = set()
    for ui in user_ingredients:
        norm = _normalize_user(ui)
        candidates |= _INGREDIENT_INDEX.get(norm, set())
        for word in _words(norm):
            candidates |= _INGREDIENT_INDEX.get(word, set())
        for canonical in SYNONYMS.get(norm, []):
            candidates |= _INGREDIENT_INDEX.get(canonical.lower(), set())
            for word in _words(canonical):
                candidates |= _INGREDIENT_INDEX.get(word, set())
    return candidates


def _user_norms(user_ingredients: list[str]) -> list[tuple[str, frozenset[str]]]:
    """Normalize user ingredients once, returning (normalized_lower, word_set) pairs."""
    result = []
    for ui in user_ingredients:
        norm = _normalize_user(ui)
        result.append((norm, _words(norm)))
    return result


def _ing_matches(
    recipe_norm: str,
    recipe_words: frozenset[str],
    user_norms: list[tuple[str, frozenset[str]]],
) -> bool:
    # Exact match
    for user_norm, _ in user_norms:
        if recipe_norm == user_norm:
            return True

    # Synonym expansion must run before the pantry guard so e.g. "shrimp paste"
    # can match "belacan" even though "belacan" is a canonical pantry item.
    for user_norm, _ in user_norms:
        for canonical in SYNONYMS.get(user_norm, []):
            canon_lower = canonical.lower()
            if recipe_norm == canon_lower or (recipe_words & _words(canon_lower)):
                return True

    # Pantry guard: canonical items that didn't exact- or synonym-match must not
    # match via loose word overlap (prevents "grated coconut" ≠ "coconut milk").
    if recipe_norm in _PANTRY_LOWER:
        return False

    if not recipe_words:
        return False

    for user_norm, user_words in user_norms:
        shared = recipe_words & user_words
        # Single-word user ingredients can match on any shared word (e.g. "pork" → "pork belly").
        # Multi-word user ingredients require ≥2 shared words so that incidental overlap like
        # "kaffir lime leaves" matching "lime juice" via "lime" is rejected.
        if shared and (len(user_words) <= 1 or len(shared) >= 2):
            return True
    return False


def score_recipe(
    recipe: dict, recipe_idx: int, user_ingredients: list[str]
) -> dict | None:
    """Return recipe dict augmented with match metadata, or None if nothing matches."""
    u_norms = _user_norms(user_ingredients)
    matched, missing = [], []
    for raw_ing, norm_ing, words_ing in _RECIPE_INGREDIENTS[recipe_idx]:
        if _ing_matches(norm_ing, words_ing, u_norms):
            matched.append(raw_ing)
        else:
            missing.append(raw_ing)

    total = len(matched) + len(missing)
    if not matched:
        return None

    pct = round(len(matched) / total * 100)
    return {
        **recipe,
        "match_pct": pct,
        "matched_count": len(matched),
        "total_count": total,
        "matched": matched,
        "missing": missing,
    }

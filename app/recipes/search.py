import re

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
    # Coriander / cilantro
    "cilantro": ["coriander"],
    "coriander leaves": ["coriander"],
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


def _words(text: str) -> set[str]:
    tokens = re.sub(r"[^a-z\s]", "", text.lower()).split()
    return {t for t in tokens if t not in _STOP_WORDS and len(t) > 1}


def ingredient_matches(recipe_ingredient: str, user_ingredients: list[str]) -> bool:
    ri_words = _words(recipe_ingredient)
    if not ri_words:
        return False
    for ui in user_ingredients:
        if ri_words & _words(ui):
            return True
        for canonical in SYNONYMS.get(ui.lower().strip(), []):
            if ri_words & _words(canonical):
                return True
    return False


def score_recipe(recipe: dict, user_ingredients: list[str]) -> dict | None:
    """Return recipe dict augmented with match metadata, or None if nothing matches."""
    matched, missing = [], []
    for ing in recipe["ingredients"]:
        if ingredient_matches(ing, user_ingredients):
            matched.append(ing)
        else:
            missing.append(ing)

    total = len(recipe["ingredients"])
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

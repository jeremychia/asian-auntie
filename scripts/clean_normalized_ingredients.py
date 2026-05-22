"""Clean up normalized_ingredients in app/recipes/data.py.

Applies in order:
  1. Lowercase + strip whitespace
  2. Drop empty strings and strings starting with '+'
  3. Strip kikkoman® brand prefix
  4. Apply explicit renames (typos, plurals, brand→generic, junk→"" to drop)
  5. Drop universal staples (water, salt, plain oil, generic sugar, black pepper)
  6. Deduplicate while preserving order

Run once:
    uv run python scripts/clean_normalized_ingredients.py
"""

import ast
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from pipeline.store import emit_data_py

# Map to "" to drop the ingredient entirely.
# Applied after lowercasing. Order doesn't matter — dict lookup.
RENAMES: dict[str, str] = {
    # ── Typos ────────────────────────────────────────────────────────────────
    "while pepper": "white pepper",
    "whole whaet flour": "whole wheat flour",
    "spash of water to help blend": "",
    # ── Brand → generic ──────────────────────────────────────────────────────
    "kikkoman® oyster sauce": "oyster sauce",
    "kikkoman® sesame oil": "sesame oil",
    "kikkoman® light soy sauce": "light soy sauce",
    "kikkoman® dark soy sauce": "dark soy sauce",
    "kikkoman® soy sauce": "soy sauce",
    "kikkoman® tamari": "tamari",
    "kikkoman® tamari soy sauce": "tamari soy sauce",
    "kikkoman® hoisin sauce": "hoisin sauce",
    "kikkoman® black bean sauce with garlic": "black bean sauce",
    "kikkoman® vegetarian oyster sauce": "vegetarian oyster sauce",
    # ── Soy sauce variants ────────────────────────────────────────────────────
    "soy sauce": "light soy sauce",
    "tamari soy sauce": "tamari",
    # ── Spring onion / green onion / scallion (all the same) ─────────────────
    "green onion": "spring onions",
    "green onions": "spring onions",
    "green onion white": "spring onions",
    "green onion whites": "spring onions",
    "chopped green onions": "spring onions",
    "spring onion": "spring onions",
    "spring onion bulb": "spring onions",
    "scallions": "spring onions",
    "scallion": "spring onions",
    # ── Onion variants ────────────────────────────────────────────────────────
    "onions": "onion",
    "chopped onion": "onion",
    "chopped onions": "onion",
    "finely chopped onion": "onion",
    "medium onion": "onion",
    "yellow onion": "onion",
    "white onion": "onion",
    "pearl onions": "onion",
    "red onions": "red onion",
    "red onion slices": "red onion",
    "small red onion": "red onion",
    "red shallot": "shallots",
    "shallot": "shallots",
    # ── Garlic / ginger forms ─────────────────────────────────────────────────
    "garlic cloves": "garlic",
    "chopped garlic": "garlic",
    "minced garlic": "garlic",
    "whole head of garlic": "garlic",
    "garlic confit": "garlic",
    "garlic confit with it's oil": "garlic",
    "garlic salt": "garlic",
    "garlic powder": "garlic",
    "ginger slices": "ginger",
    "ginger slice": "ginger",
    "fresh ginger slices": "ginger",
    "shredded ginger": "ginger",
    "fresh ginger juice": "ginger",
    "minced ginger": "ginger",
    "inch ginger": "ginger",
    "thick ginger piece": "ginger",
    "grated ginger": "ginger",
    "ginger garlic paste": "ginger",
    # ── Bell peppers ──────────────────────────────────────────────────────────
    "bell pepper": "red bell pepper",
    "bell peppers": "red bell pepper",
    "red pepper": "red bell pepper",
    "mini bell pepper": "red bell pepper",
    "mini orange sweet pepper": "red bell pepper",
    "mini red sweet pepper": "red bell pepper",
    "mini sweet pepper": "red bell pepper",
    "mini sweet peppers": "red bell pepper",
    "green pepper": "green bell pepper",
    "chopped capsicum": "capsicum",
    "green capsicum": "capsicum",
    # ── Chillies ──────────────────────────────────────────────────────────────
    "green chilli": "green chillies",
    "fresh chilies": "green chillies",
    "bullet chillies": "green chillies",
    "chilli powder": "red chilli powder",
    "roasted chili powder": "red chilli powder",
    "dried red chillies": "dried chillies",
    "dried red chili": "dried chillies",
    "dried red chilli": "dried chillies",
    "dried chili pepper": "dried chillies",
    "dried chili peppers": "dried chillies",
    "dried red chilies": "dried chillies",
    "dry red chili peppers": "dried chillies",
    "dry red chilli": "dried chillies",
    "red chili pepper": "dried chillies",
    "chao tian jiao pepper": "dried chillies",
    "dried chili flakes": "chilli flakes",
    "toasted chili flakes": "chilli flakes",
    "sichuan dried chili flakes": "chilli flakes",
    "crushed red pepper": "chilli flakes",
    "red pepper flakes": "chilli flakes",
    "sichuan peppercorns": "sichuan peppercorn",
    "black peppercorns": "",
    "white pepper powder": "white pepper",
    # ── Turmeric ──────────────────────────────────────────────────────────────
    "turmeric powder": "turmeric",
    "ground turmeric": "turmeric",
    # ── Spice misc ────────────────────────────────────────────────────────────
    "curry spice": "curry powder",
    "ground cardamom": "cardamom",
    "coriander powder": "coriander",
    "ground coriander seeds": "coriander",
    "inch cinnamon": "cinnamon",
    "cinnamon sticks": "cinnamon",
    "three-inch cinnamon stick": "cinnamon",
    "five-spice powder": "five spice powder",
    # ── Vinegar variants ──────────────────────────────────────────────────────
    "chinkiang vinegar": "black vinegar",
    "zhenjiang black vinegar": "black vinegar",
    "sweet black vinegar": "black vinegar",
    "rice wine vinegar": "rice vinegar",
    "white rice vinegar": "rice vinegar",
    # ── Bean sauces / fermented ───────────────────────────────────────────────
    "black bean paste": "black bean sauce",
    "black bean sauce with garlic": "black bean sauce",
    "fermented black bean sauce": "fermented black beans",
    "dried fermented black bean": "fermented black beans",
    "doubanjiang": "chilli bean paste",
    # ── Cooking wine ──────────────────────────────────────────────────────────
    "chinese cooking wine": "cooking wine",
    "rice cooking wine": "cooking wine",
    "shaoxing cooking wine": "shaoxing wine",
    "shaoxing rice wine": "shaoxing wine",
    # ── Oil variants ──────────────────────────────────────────────────────────
    "extra virgin olive oil": "olive oil",
    "more olive oil": "olive oil",
    "cooking oil": "vegetable oil",
    "corn oil": "vegetable oil",
    "canola oil": "vegetable oil",
    "chicken oil": "vegetable oil",
    "yóu yóu tea seed oil": "vegetable oil",
    # ── Sweeteners ────────────────────────────────────────────────────────────
    "dark brown sugar": "brown sugar",
    "jaggery": "palm sugar",
    "gula melaka": "palm sugar",
    "monk fruit sweetener": "",
    "monkfruit sweetener": "",
    "hot honey": "honey",
    "maltose": "honey",
    "maltose/honey": "honey",
    # ── Acids / citrus ────────────────────────────────────────────────────────
    "calamansi lime juice": "lime juice",
    "juice of lemon": "lemon juice",
    "juice of lemons": "lemon juice",
    "lemon slices": "lemon juice",
    "slice of lemon": "lemon juice",
    "lime juice from ½ lime": "lime juice",
    "tamarind pulp": "tamarind paste",
    # ── Coconut / pandan ──────────────────────────────────────────────────────
    "coconut cream": "coconut milk",
    "pandan juice": "pandan leaves",
    "pandan extract": "pandan leaves",
    # ── Noodles ───────────────────────────────────────────────────────────────
    "fresh egg noodle": "egg noodles",
    "wonton noodles": "egg noodles",
    "lo mein": "egg noodles",
    "chow mein noodles": "egg noodles",
    "fresh chow mein noodles": "egg noodles",
    "thick chow mein noodles": "egg noodles",
    "hong kong style pan fried noodles": "egg noodles",
    "hong kong style pan-fried noodles": "egg noodles",
    "thick noodle": "egg noodles",
    "yee mein": "egg noodles",
    "yee mein noodles": "egg noodles",
    "yellow noodles": "egg noodles",
    "dried noodles": "egg noodles",
    "fresh chow fun": "flat rice noodles",
    "fresh flat rice noodles": "flat rice noodles",
    "fresh rice noodle": "rice noodles",
    "fresh wide rice noodles": "rice noodles",
    "rice noodle rolls": "rice noodles",
    "rice stick noodles": "rice noodles",
    "fresh rice rolls": "rice noodles",
    "dried rice vermicelli": "rice vermicelli",
    "dried vermicelli noodles": "rice vermicelli",
    "vermicelli noodle": "rice vermicelli",
    "vermicelli noodles": "rice vermicelli",
    "vermicelli": "rice vermicelli",
    "mung bean vermicelli": "glass noodles",
    "dried spaghetti": "spaghetti",
    "dry spaghetti": "spaghetti",
    "dry pasta of choice": "pasta",
    "whole wheat pasta": "pasta",
    # ── Rice ──────────────────────────────────────────────────────────────────
    "uncooked jasmine rice": "jasmine rice",
    "thai jasmine rice": "jasmine rice",
    "thai rice": "jasmine rice",
    "long grain rice": "jasmine rice",
    "broken rice": "jasmine rice",
    "white rice": "jasmine rice",
    "medium-grain brown rice": "brown rice",
    "glutinous / sticky rice": "glutinous rice",
    "regular rice flour": "rice flour",
    # ── Tofu ──────────────────────────────────────────────────────────────────
    "medium firm tofu": "firm tofu",
    "block tofu": "tofu",
    "dried tofu": "dried bean curd",
    "five-spice dried bean curd": "dried bean curd",
    "fried tofu puff": "tofu",
    # ── Mushrooms ────────────────────────────────────────────────────────────
    "fresh mushroom": "mushrooms",
    "mushroom stems": "mushrooms",
    "beech mushroom": "button mushrooms",
    "brown button mushroom": "button mushrooms",
    "large button mushrooms": "button mushrooms",
    "butter mushrooms": "button mushrooms",
    "pack button mushrooms": "button mushrooms",
    "white mushroom": "button mushrooms",
    "enoki mushroom": "king oyster mushroom",
    "white shimeji mushroom": "seafood mushroom",
    "shimeji mushrooms": "seafood mushroom",
    "seafood mushrooms": "seafood mushroom",
    "fresh shiitake mushrooms": "fresh shiitake mushroom",
    "dried wood ear mushroom": "wood ear mushrooms",
    "rehydrated wood ear fungus": "wood ear mushrooms",
    "cloud ear fungus": "dried cloud ear fungus",
    # ── Produce ───────────────────────────────────────────────────────────────
    "carrots": "carrot",
    "small carrot": "carrot",
    "tomatoes": "tomato",
    "chopped tomatoes": "tomato",
    "tomato slices": "tomato",
    "roma tomatoes or 10 grape tomatoes": "tomato",
    "medium-sized tomato": "tomato",
    "cherry tomato": "cherry tomatoes",
    "cucumber slices": "cucumber",
    "sliced cucumber": "cucumber",
    "fresh cucumbers": "cucumber",
    "cucumbers": "cucumber",
    "avocados": "avocado",
    "mangoes": "mango",
    "ripe mango": "mango",
    "limes": "lime",
    "sweetcorn": "sweet corn",
    "sweet corn filling": "sweet corn",
    "unsweetened corn": "sweet corn",
    "frozen corn and peas": "sweet corn",
    "whole baby corn": "baby corn",
    "green pea": "green peas",
    "sugar snap peas": "snow pea",
    "red cabbage": "cabbage",
    "green cabbage": "cabbage",
    "chopped cabbage": "cabbage",
    "julienned green or purple cabbage": "cabbage",
    "daikon radish": "daikon",
    "white radish": "daikon",
    "chinese turnip": "daikon",
    "dried radish": "daikon",
    "red radishes": "daikon",
    "radish": "daikon",
    "broccoli stem": "broccoli",
    "aubergine": "eggplant",
    "brinjal": "eggplant",
    "chinese eggplant": "eggplant",
    "medium eggplants or 1 large eggplant": "eggplant",
    "ong choy": "kangkung",
    "okras": "okra",
    "choy sum": "chinese broccoli",
    "bean sprout": "bean sprouts",
    "beansprout": "bean sprouts",
    "moong bean sprouts": "bean sprouts",
    "green bean": "green beans",
    "french beans": "green beans",
    "chopped green beans": "green beans",
    "lettuce leaves": "lettuce",
    "romaine lettuce": "lettuce",
    "celery stalk": "celery",
    "bay leaf": "bay leaves",
    "lemongrass stalk": "lemongrass stalks",
    "dried mandarin peel": "dried mandarin orange peel",
    "rehydrated dried mandarin peel": "dried mandarin orange peel",
    "potato": "potato",
    "potatoes": "potato",
    "red potatoes": "potato",
    "russet potatoes": "potato",
    # ── Protein ───────────────────────────────────────────────────────────────
    "chicken meat": "chicken",
    "minced chicken": "chicken",
    "minced chicken/pork/beef": "chicken",
    "whole chicken": "chicken",
    "bone-in chicken thigh": "chicken thigh",
    "chicken thighs": "chicken thigh",
    "skin-on, bone-in chicken breast": "chicken breast",
    "chicken drumstick meat": "chicken drumstick",
    "chicken wing": "chicken wings",
    "chicken powder": "chicken bouillon",
    "chicken bouillon powder": "chicken bouillon",
    "chicken broth": "chicken stock",
    "stock cube": "chicken bouillon",
    "lean pork": "pork",
    "pork loin": "pork",
    "pork loin sirloin chop": "pork chop",
    "cured pork belly": "pork belly",
    "pork shoulder butt": "pork shoulder",
    "spare ribs": "pork ribs",
    "pork rib": "pork ribs",
    "beef brisket": "beef",
    "beef flank": "beef",
    "corned beef": "beef",
    "flank steak": "beef",
    "new york strip steak": "beef",
    "steak": "beef",
    "oxtail": "beef",
    "ground beef": "beef",
    "prawn": "shrimp",
    "prawns": "shrimp",
    "head-on shrimp": "shrimp",
    "fresh/thawed shrimp": "shrimp",
    "large dried shrimp": "dried shrimp",
    "imitation crab": "crab",
    "tilapia fish fillets": "tilapia",
    "sole fish filet": "sole fish",
    "boneless fish fillets": "fish fillet",
    "tonguefish fillet": "fish fillet",
    "wild alaskan pacific cod": "fish fillet",
    "whole catfish": "fish fillet",
    "whole fish": "fish fillet",
    "lobster tail": "lobster",
    "whole lobster": "lobster",
    # ── Nuts ──────────────────────────────────────────────────────────────────
    "peanut": "peanuts",
    "roasted peanuts": "peanuts",
    "fried or roasted peanuts": "peanuts",
    "raw peanut": "peanuts",
    "peanut powder": "peanuts",
    "roasted cashew": "cashews",
    # ── Dairy / cheese ───────────────────────────────────────────────────────
    "mozzarella": "mozzarella cheese",
    "grated mozzarella": "mozzarella cheese",
    "small cubes mozzarella cheese": "mozzarella cheese",
    "parmesan": "parmesan cheese",
    "grated parmesan": "parmesan cheese",
    "cube processed cheese": "processed cheese",
    "cubes processed cheese": "processed cheese",
    "grated processed cheese": "processed cheese",
    "cheese slice": "processed cheese",
    "cheese slices": "processed cheese",
    "grated cheese of choice": "processed cheese",
    "grated cheese: parmesan processed or even more feta": "processed cheese",
    "cheese of choice": "processed cheese",
    "cheddar cheese slices": "cheddar cheese",
    "white cheddar cheese": "cheddar cheese",
    "grated cheddar cheese": "cheddar cheese",
    "fresh cottage cheese": "cottage cheese",
    "paneer cubes": "paneer",
    "thick slices paneer": "paneer",
    "spicy fried paneer": "paneer",
    "block high protein low fat paneer": "paneer",
    "paneer cheese filling": "paneer",
    "fresh cream": "heavy cream",
    "hung curd": "curd",
    "unflavoured curd": "curd",
    "high protein yogurt or curd": "curd",
    "curd/yogurt": "curd",
    "curd topped with salt and roasted cumin powder": "curd",
    "softened butter": "butter",
    "unsalted butter": "butter",
    "garlic butter": "butter",
    "salted butter": "butter",
    "butter to toast": "butter",
    "salted butter per slice of bread": "butter",
    # ── Eggs ─────────────────────────────────────────────────────────────────
    "egg white": "egg whites",
    "hard-boiled egg": "hard-boiled eggs",
    "salted egg yolk": "salted egg",
    "egg yolk": "eggs",
    "beaten egg": "eggs",
    "fresh quail eggs": "eggs",
    # ── Flour / starch ───────────────────────────────────────────────────────
    "all purpose flour": "all-purpose flour",
    "bread crumbs": "breadcrumbs",
    "fine breadcrumbs": "breadcrumbs",
    "panko breadcrumbs": "breadcrumbs",
    "tapioca flour": "tapioca starch",
    "chickpea flour": "gram flour",
    "wheat starch": "potato starch",
    # ── Wrappers / bread ──────────────────────────────────────────────────────
    "egg roll wrapper": "wonton wrappers",
    "siu mai wrappers": "wonton wrappers",
    "potsticker wrappers": "wonton wrappers",
    "rice paper": "spring roll wrappers",
    "flour tortillas": "",
    "tortillas": "",
    "bread of choice": "",
    "multiseed bread": "",
    "roti": "",
    "mini whole wheat roti": "",
    # ── Sauces / condiments ───────────────────────────────────────────────────
    "tomato ketchup": "ketchup",
    "schezwan sauce": "chilli bean paste",
    "spicy mayo": "mayonnaise",
    "tandoori mayonnaise": "mayonnaise",
    "mustard sauce": "mustard",
    "abalone juice from can": "abalone",
    "a generous grating of parmesan": "parmesan cheese",
    "vanilla essence": "vanilla extract",
    "active dry yeast": "active dry or instant yeast",
    "toasted sesame oil": "sesame oil",
    "white sesame seeds": "sesame seeds",
    "roasted sesame seeds": "sesame seeds",
    "black sesame powder": "sesame seeds",
    # ── Herbs ────────────────────────────────────────────────────────────────
    "fresh cilantro": "cilantro",
    "chopped cilantro": "cilantro",
    "chopped fresh cilantro": "cilantro",
    "fresh coriander": "coriander",
    "handful of coriander": "coriander",
    "handful of fresh coriander": "coriander",
    "fresh coriander leaves": "coriander",
    "fresh basil": "basil leaves",
    "fresh basil leaves": "basil leaves",
    "handful of fresh basil": "basil leaves",
    # ── More chilli variants ─────────────────────────────────────────────────
    "green chilies": "green chillies",
    "bird's eye chillies": "green chillies",
    "thai bird's eye chili": "green chillies",
    "thai chillies": "green chillies",
    "thai chili pepper": "green chillies",
    "few fresh chilies": "green chillies",
    "fresh green chilies": "green chillies",
    "whole green chilies": "green chillies",
    "fresno chili pepper": "green chillies",
    "chili pepper": "green chillies",
    # ── More oil variants ────────────────────────────────────────────────────
    "neutral cooking oil": "vegetable oil",
    "neutral oil": "vegetable oil",
    # ── More produce ─────────────────────────────────────────────────────────
    "small or 1 regular sweet potato": "sweet potato",
    "large sweet potato": "sweet potato",
    "medium opo squash": "bottle gourd",
    "small beetroot": "beetroot",
    "roasted beetroot": "beetroot",
    "roasted beetroot puree": "beetroot",
    # ── More protein ─────────────────────────────────────────────────────────
    "swai fish fillet": "fish fillet",
    # ── More misc ────────────────────────────────────────────────────────────
    "mini homemade bao": "",
    "whole wheat protein bread": "",
    "toasted rice": "",
    "vegetables": "",
    "tender core of banana stem or lotus roots": "",
    "sprinkle of chaat masala": "chaat masala",
    "tad of garlic chili flakes": "chilli flakes",
    "drinking rice wine": "rice wine",
    "yam": "",
    "fuzzy melon": "",
    "khapli atta": "whole wheat flour",
    "pav bhaji masala": "",
    "coconut chutney": "",
    "garlic chutney": "",
    "green chutney": "",
    "blue matcha": "",
    "pinch of black salt": "",
    "pinch of hing": "",
    "sev": "",
    "podi": "",
    "sattu": "",
    "splash of balsamic vinegar": "",
    "rice": "jasmine rice",
    # ── Utensils / non-food ───────────────────────────────────────────────────
    "non stick pan": "",
    "spatula": "",
    "parchment paper": "",
    "roll of cotton string": "",
    "metal bread tin": "",
    # ── Drop: junk / non-ingredients / too-vague ──────────────────────────────
    "vite ramen naked noods": "",
    "blue lays": "",
    "16/20 shrimp": "",
    "31/35 shrimp": "",
    "blended puree": "",
    "beans like kidney beans or black beans": "",
    "equal amount of chopped cilantro and": "",
    "fresh herbs: coriander + mint + basil": "",
    "handful of fresh herbs: basil + coriander": "",
    "green chilies and cilantro for garnish": "",
    "onion salad: thinly sliced onions + vinegar + salt + chilli powder": "",
    "roasted spice mix: 1 tbsp coriander seeds + 3 dried red chillies + 1 tsp cumin seeds": "",
    "optional add ons: ginger": "",
    "sauces or chutneys": "",
    "toppings of your choice- i used olives": "",
    "ghee or salted/white butter": "",
    "cornstarch or all-purpose flour": "",
    "lemon juice or vinegar": "",
    "homemade pav toasted with butter": "",
    "everything but the bagel seasoning": "",
    "garlic bread seasoning": "",
    "garlic herb seasoning": "",
    "dough per pizza": "",
    "chilli thecha chutney per taco": "",
    "green chutney per sandwich": "",
    "skins and fats from the chicken thighs": "",
    "chicken bones & scraps": "",
    "mango achaar with it's oil": "mango pickle",
    "millet vampoosa": "",
    "my homemade rice cakes": "",
    "vegetable pattly": "",
    "chilli bajji": "",
    "fine breadcrumbs + 1/2 tsp dried parsley": "breadcrumbs",
    "ghee to dip the litti": "ghee",
    "momo or schezwan chutney": "",
    "shacha sauce": "",
    "medium opo squash/calabash or 3 chayote squash": "",
    "boiled water": "",
    "red food coloring": "",
    "ice": "",
    "ice cubes": "",
    "soda water": "",
    "laphet or fermented tea leaves": "fermented tea leaves",
    "laphet or fermented tea leaves, unflavored": "fermented tea leaves",
    "banana blossom": "",
    "idli batter": "",
    "quinoa": "",
    "flaxseed powder": "",
    "scoop vanilla plant protein powder": "",
    "hing": "",
    "broth": "",
    # ── Water variants → drop ────────────────────────────────────────────────
    "boiling water": "",
    "cold water": "",
    "warm water": "",
    "hot water": "",
    "ice water": "",
    "boiling hot water": "",
    "hot salted water": "",
    "boiling water or vegetable stock": "",
    "water or veggie stock": "",
    "water (for blanching)": "",
    "water (for broth)": "",
    "water, for boiling": "",
    "water, for corn blend": "",
    "salted pasta water": "",
    "salty pasta water": "",
    "splash of pasta water": "",
    "pasta water": "",
}

# Strings to drop after renames (universal staples)
OMIT: set[str] = {
    "water",
    "salt",
    "sea salt",
    "flaky sea salt",
    "pinch of salt",
    "salt & pepper",
    "salt and pepper",
    "salt pepper",
    "oil",
    "oil for frying",
    "oil to fry",
    "oil, for cooking chicken",
    "oil, for cooking vegetables",
    "sugar",
    "white sugar",
    "granulated sugar",
    "black pepper",
    "ground black pepper",
}

_KIKKOMAN_RE = re.compile(r"^kikkoman[®]?\s*", re.IGNORECASE)


def clean_ingredient(raw: str) -> str | None:
    """Return cleaned ingredient name, or None to drop it."""
    s = raw.strip().lower()

    if not s:
        return None

    # Drop strings starting with '+' (measurement fragments)
    if s.startswith("+"):
        return None

    # Strip kikkoman® brand prefix (catch any kikkoman-prefixed entry not in RENAMES)
    s = _KIKKOMAN_RE.sub("", s).strip()

    # Apply explicit renames
    if s in RENAMES:
        s = RENAMES[s]
        if not s:
            return None

    # Drop universal staples
    if s in OMIT:
        return None

    return s or None


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def main() -> None:
    data_path = pathlib.Path(__file__).parent.parent / "app" / "recipes" / "data.py"
    src = data_path.read_text()

    tree = ast.parse(src)
    recipes = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "RECIPES":
                    recipes = ast.literal_eval(node.value)
                    break

    if recipes is None:
        print("ERROR: could not find RECIPES in data.py", file=sys.stderr)
        sys.exit(1)

    cleaned = []
    total_before = 0
    total_after = 0
    for recipe in recipes:
        original = recipe.get("normalized_ingredients", [])
        total_before += len(original)
        processed = [clean_ingredient(i) for i in original]
        filtered = _dedup([i for i in processed if i is not None])
        total_after += len(filtered)
        cleaned.append({**recipe, "normalized_ingredients": filtered})

    output = emit_data_py(cleaned, source="scripts/normalize_recipe_data.py")
    output = output.replace(
        "# Generated by scripts/normalize_recipe_data.py — do not edit by hand.\n",
        "# Run scripts/normalize_recipe_data.py after adding entries to refresh normalized_ingredients.\n",
    )
    data_path.write_text(output)
    print(
        f"Wrote {len(cleaned)} recipes  |  "
        f"normalized_ingredients: {total_before} → {total_after} "
        f"({total_before - total_after} removed)"
    )


if __name__ == "__main__":
    main()
